"""Real subprocess lifecycle checks; no agent or model inference is invoked."""

from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import threading
import time
from contextlib import suppress
from pathlib import Path
from types import SimpleNamespace

import pytest
from tee.docagents import runner


def _plan(tmp_path: Path, *scripts: str, backend: str = "aider", stdin: str | None = None):
    return SimpleNamespace(
        commands=[[sys.executable, "-c", script] for script in scripts],
        cwd=tmp_path,
        env={"PATH": os.defpath, "DOCAGENT_TEST_ONLY": "present"},
        stdin=stdin,
        backend=backend,
        model="fixture-model",
        paid=False,
    )


def _wait_for(predicate, timeout: float = 3) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            pytest.fail("owned subprocess did not reach the expected state")
        time.sleep(0.01)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # An orphan zombie is already terminated; its reaper belongs to the host.
    output = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    ).stdout.strip()
    return bool(output) and not output.startswith("Z")


def _thread_run(worker, plan, run_dir, **kwargs):
    results = []
    thread = threading.Thread(target=lambda: results.append(worker.run(plan, run_dir, **kwargs)))
    thread.start()
    return thread, results


def test_success_private_bounded_logs_stdin_and_no_environment_inheritance(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCAGENT_HOST_SECRET", "must-not-inherit")
    script = """
import os, sys
assert 'DOCAGENT_HOST_SECRET' not in os.environ
assert os.environ['DOCAGENT_TEST_ONLY'] == 'present'
assert len(sys.stdin.read()) == 500_000
print('fixture-model-secret-content')
print('stderr included', file=sys.stderr)
"""
    run_dir = tmp_path / "run"
    result = runner.Worker().run(_plan(tmp_path, script, stdin="x" * 500_000), run_dir)
    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert result["backend"] == "aider"
    assert result["model"] == "fixture-model"
    assert result["paid"] is False
    assert "fixture-model-secret-content" not in json.dumps(result)
    assert "stderr included" in (run_dir / "worker.log").read_text()
    assert (run_dir / "worker.log").read_bytes() == (run_dir / "final.log").read_bytes()
    assert stat.S_IMODE(run_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE((run_dir / "worker.log").stat().st_mode) == 0o600
    assert stat.S_IMODE((run_dir / "final.log").stat().st_mode) == 0o600
    assert not list(run_dir.glob("tmp*"))


def test_stdin_is_a_pipe_and_simultaneous_output_cannot_deadlock(tmp_path):
    script = """
import os, stat, sys
assert stat.S_ISFIFO(os.fstat(0).st_mode)
os.write(1, b'x' * 200_000)
assert len(sys.stdin.read()) == 500_000
print('finished both directions')
"""
    run_dir = tmp_path / "run"
    result = runner.Worker().run(_plan(tmp_path, script, stdin="p" * 500_000), run_dir)
    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert (run_dir / "worker.log").read_text().endswith("finished both directions\n")


def test_stdin_backpressure_cannot_block_deadline_or_cleanup(tmp_path):
    plan = _plan(tmp_path, "import time; time.sleep(30)", stdin="p" * 500_000)
    result = runner.Worker().run(plan, tmp_path / "run", timeout_s=0.15)
    assert result["reason"] == "timeout"
    assert result["exit_code"] < 0
    assert result["wall_s"] < 2


def test_darwin_group_probe_eperm_while_waitpid_lags_still_reaps(tmp_path, monkeypatch):
    """Darwin can report an unsignalable zombie before poll observes its exit."""
    original_killpg = os.killpg
    original_popen = subprocess.Popen
    probe_seen = threading.Event()
    children = []

    def darwin_killpg(pid, sig):
        if sig == 0 and not probe_seen.is_set():
            probe_seen.set()
            raise PermissionError(1, "Operation not permitted")
        return original_killpg(pid, sig)

    def delayed_waitpid(*args, **kwargs):
        proc = original_popen(*args, **kwargs)
        children.append(proc)
        original_poll = proc.poll
        delayed = False

        def poll():
            nonlocal delayed
            if probe_seen.is_set() and not delayed:
                delayed = True
                return None
            return original_poll()

        proc.poll = poll
        return proc

    monkeypatch.setattr(runner.os, "killpg", darwin_killpg)
    monkeypatch.setattr(runner.subprocess, "Popen", delayed_waitpid)
    try:
        result = runner.Worker().run(
            _plan(tmp_path, "import time; time.sleep(30)", stdin="p" * 500_000),
            tmp_path / "run",
            timeout_s=0.15,
        )
        assert probe_seen.is_set()
        assert result["reason"] == "timeout"
        assert result["exit_code"] == -signal.SIGTERM
        assert children[0].returncode == -signal.SIGTERM
    finally:
        for proc in children:
            with suppress(ProcessLookupError, PermissionError):
                original_killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=1)


def test_worker_closing_stdin_early_does_not_raise_or_leak_pipe(tmp_path):
    plan = _plan(tmp_path, "import os; os.close(0); print('done')", stdin="p" * 500_000)
    result = runner.Worker().run(plan, tmp_path / "run")
    assert result["ok"] is True
    assert result["exit_code"] == 0


def test_setup_does_not_receive_final_stdin(tmp_path):
    plan = _plan(
        tmp_path,
        "import sys; assert sys.stdin.read() == ''; print('setup')",
        "import sys; assert sys.stdin.read() == 'final prompt'; print('final')",
        stdin="final prompt",
    )
    run_dir = tmp_path / "run"
    result = runner.Worker().run(plan, run_dir)
    assert result["ok"] is True
    assert (run_dir / "worker.log").read_text() == "setup\nfinal\n"
    assert (run_dir / "final.log").read_text() == "final\n"


@pytest.mark.parametrize("setup", [False, True])
def test_nonzero_exit_and_setup_failure_never_execute_next_command(tmp_path, setup):
    fail = "import sys; print('sensitive failure'); sys.exit(7)"
    scripts = (
        (fail, "from pathlib import Path; Path('should-not-run').touch()") if setup else (fail,)
    )
    result = runner.Worker().run(_plan(tmp_path, *scripts), tmp_path / "run")
    assert result["ok"] is False
    assert result["reason"] == ("setup_failed" if setup else "worker_failed")
    assert result["exit_code"] == 7
    assert "sensitive failure" not in json.dumps(result)
    assert not (tmp_path / "should-not-run").exists()


def test_stdout_flood_stops_at_cap_and_kills_term_ignoring_worker(tmp_path):
    script = """
import os, signal
signal.signal(signal.SIGTERM, signal.SIG_IGN)
while True:
    os.write(1, b'x' * 65536)
"""
    run_dir = tmp_path / "run"
    result = runner.Worker().run(_plan(tmp_path, script), run_dir, timeout_s=3)
    assert result["ok"] is False
    assert result["reason"] == "output_limit"
    assert result["exit_code"] == -signal.SIGKILL
    assert result["wall_s"] < 3
    assert (run_dir / "worker.log").stat().st_size == runner.MAX_LOG_BYTES
    assert (run_dir / "final.log").stat().st_size == runner.MAX_LOG_BYTES


def test_output_limit_is_shared_across_setup_and_final(tmp_path):
    plan = _plan(
        tmp_path,
        "import os; os.write(1, b'x' * 600_000)",
        "import os; os.write(1, b'x' * 600_000)",
    )
    run_dir = tmp_path / "run"
    result = runner.Worker().run(plan, run_dir)
    assert result["reason"] == "output_limit"
    assert (run_dir / "worker.log").stat().st_size == runner.MAX_LOG_BYTES
    assert (run_dir / "final.log").stat().st_size == runner.MAX_LOG_BYTES - 600_000


def test_whole_run_deadline_includes_setup_time(tmp_path):
    plan = _plan(
        tmp_path,
        "import time; time.sleep(0.08); print('setup done')",
        "import time; time.sleep(1); print('too late')",
    )
    result = runner.Worker().run(plan, tmp_path / "run", timeout_s=0.2)
    assert result["reason"] == "timeout"
    assert result["exit_code"] < 0
    assert result["wall_s"] < 2


def test_cancellation_before_run_never_spawns(tmp_path, monkeypatch):
    worker = runner.Worker()
    worker.cancel()

    def forbidden_spawn(*args, **kwargs):
        pytest.fail("cancelled run spawned a process")

    monkeypatch.setattr(runner.subprocess, "Popen", forbidden_spawn)
    result = worker.run(_plan(tmp_path, "print('not executed')"), tmp_path / "run")
    assert result["ok"] is False
    assert result["reason"] == "cancelled"
    assert not (tmp_path / "run").exists()


def test_cancellation_during_spawn_cannot_miss_owned_process(tmp_path, monkeypatch):
    worker = runner.Worker()
    original_popen = subprocess.Popen
    created = threading.Event()
    release = threading.Event()
    children = []

    def delayed_popen(*args, **kwargs):
        proc = original_popen(*args, **kwargs)
        children.append(proc)
        created.set()
        assert release.wait(3)
        return proc

    monkeypatch.setattr(runner.subprocess, "Popen", delayed_popen)
    thread, results = _thread_run(
        worker, _plan(tmp_path, "import time; time.sleep(30)"), tmp_path / "run"
    )
    assert created.wait(3)
    canceller = threading.Thread(target=worker.cancel)
    canceller.start()
    _wait_for(worker._cancelled.is_set)
    release.set()
    thread.join(3)
    canceller.join(3)
    assert not thread.is_alive()
    assert not canceller.is_alive()
    assert results[0]["reason"] == "cancelled"
    assert children[0].returncode is not None
    assert worker._proc is None


@pytest.mark.parametrize("finish_normally", [False, True])
def test_background_group_terminated_on_cancel_and_normal_exit(tmp_path, finish_normally):
    child_code = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
    script = f"""
import json, os, subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', {child_code!r}])
Path('owned-pids.json').write_text(json.dumps([os.getpid(), child.pid]))
{'print("completed")' if finish_normally else "time.sleep(30)"}
"""
    worker = runner.Worker()
    thread, results = _thread_run(worker, _plan(tmp_path, script), tmp_path / "run")
    pids_file = tmp_path / "owned-pids.json"
    _wait_for(pids_file.exists)
    pids = json.loads(pids_file.read_text())
    try:
        if not finish_normally:
            worker.cancel()
        thread.join(3)
        assert not thread.is_alive()
        assert results[0]["ok"] is finish_normally
        if not finish_normally:
            assert results[0]["reason"] == "cancelled"
        for pid in pids:
            _wait_for(lambda pid=pid: not _alive(pid))
    finally:
        worker.cancel()
        for pid in pids:
            with suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
        thread.join(3)


def test_existing_log_cannot_be_overwritten_or_followed(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    sensitive = tmp_path / "sensitive"
    sensitive.write_text("keep")
    (run_dir / "worker.log").symlink_to(sensitive)
    result = runner.Worker().run(_plan(tmp_path, "print('unused')"), run_dir)
    assert result["reason"] == "worker_io_error"
    assert sensitive.read_text() == "keep"


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True, "300"])
def test_invalid_deadline_refuses_before_spawn(tmp_path, timeout):
    result = runner.Worker().run(_plan(tmp_path, "print('unused')"), tmp_path / "run", timeout)
    assert result["reason"] == "invalid_timeout"
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize(
    ("finish", "ok", "reason"),
    [
        ("completed", True, "cline_completed"),
        ("aborted", False, "cline_not_completed"),
        (None, False, "cline_completion_missing"),
    ],
)
def test_cline_requires_completed_terminal_event_not_just_zero_exit(tmp_path, finish, ok, reason):
    event = {"type": "run_result", "finishReason": finish, "text": "secret model response"}
    output = json.dumps(event) if finish else "ordinary output"
    result = runner.Worker().run(
        _plan(tmp_path, f"print({output!r})", backend="cline"), tmp_path / "run"
    )
    assert result["exit_code"] == 0
    assert result["ok"] is ok
    assert result["reason"] == reason
    assert result["usage"] is None
    assert "secret model response" not in json.dumps(result)


def test_setup_terminal_event_cannot_certify_incomplete_final_run(tmp_path):
    completed = json.dumps({"type": "run_result", "finishReason": "completed"})
    plan = _plan(tmp_path, f"print({completed!r})", "print('no terminal event')", backend="cline")
    result = runner.Worker().run(plan, tmp_path / "run")
    assert result["ok"] is False
    assert result["reason"] == "cline_completion_missing"


def test_cancellation_during_completion_validation_wins(tmp_path, monkeypatch):
    from tee.docagents import backends

    worker = runner.Worker()

    def completion(log_path, exit_code, *, backend):
        worker.cancel()
        return {"ok": True, "reason": "completed"}

    monkeypatch.setattr(backends, "final_success", completion)
    result = worker.run(_plan(tmp_path, "print('done')"), tmp_path / "run")
    assert result["exit_code"] == 0
    assert result["ok"] is False
    assert result["reason"] == "cancelled"


def test_missing_executable_reports_compact_failure_without_argv(tmp_path):
    plan = _plan(tmp_path, "unused")
    plan.commands = [[str(tmp_path / "missing-program"), "secret argument"]]
    result = runner.Worker().run(plan, tmp_path / "run")
    assert result["reason"] == "worker_io_error"
    assert "secret argument" not in json.dumps(result)
    assert "missing-program" not in json.dumps(result)
