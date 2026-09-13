"""Orderly shutdown owns solver cleanup, including already queued work."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.jobs import JobManager
from tee.structural import runner
from tee.structural.examples import cantilever
from tee.structural.model import StructuralError
from tee.structural.service import StructuralService


def wait_for(predicate: Any, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            pytest.fail("Timed out waiting for structural shutdown test state.")
        time.sleep(0.01)


def test_app_shutdown_stops_real_owned_solver_and_descendant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    service = StructuralService(tmp_path)
    app.structural = service
    model = service.save(cantilever())
    started = threading.Event()
    paths: list[Path] = []
    pids: dict[str, int] = {}

    def slow_solver(
        root: Path, m: dict, loads: dict, engine: str, cfg: dict, cancelled: threading.Event
    ) -> dict:
        script = root / "slow.py"
        script.write_text(
            "import json,os,signal,subprocess,sys,time\n"
            "from pathlib import Path\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "child = subprocess.Popen([sys.executable, '-c', "
            "'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'])\n"
            "Path('pids.json').write_text(json.dumps({'parent':os.getpid(),'child':child.pid}))\n"
            "time.sleep(60)\n"
        )
        paths.append(root)
        started.set()
        return runner.execute([sys.executable, str(script)], root, cancelled, 60)

    monkeypatch.setattr(runner, "executable", lambda *args: (Path(sys.executable), None))
    monkeypatch.setattr(runner, "solve", slow_solver)
    stop = threading.Event()
    job = app.jobs.submit(
        "st_solve",
        lambda: service.solve(model["model_id"], 1, "vertical", "openseespy", stop),
        on_cancel=stop.set,
    )
    try:
        assert started.wait(5)
        wait_for(lambda: (paths[0] / "pids.json").exists())
        pids = json.loads((paths[0] / "pids.json").read_text())
        before = time.monotonic()
        app.shutdown()
        assert time.monotonic() - before < 5
        assert stop.is_set()
        wait_for(lambda: next(j for j in app.jobs.list() if j["job"] == job)["state"] == "error")
        assert "cancelled" in next(j for j in app.jobs.list() if j["job"] == job)["error"]
        with pytest.raises(ProcessLookupError):
            os.kill(pids["parent"], 0)

        def child_stopped() -> bool:
            state = subprocess.run(
                ["ps", "-o", "stat=", "-p", str(pids["child"])],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            return not state or state.startswith("Z")

        # An orphan can remain a zombie until the OS reaps it; it must not run.
        wait_for(child_stopped)
        assert (paths[0] / "failure.json").exists()
        assert not (paths[0] / "result.json").exists()
        with pytest.raises(StructuralError, match="shutting down"):
            service.solve(model["model_id"], 1, "vertical", "openseespy", threading.Event())
        service.close()  # Repeated orderly close is safe.
    finally:
        stop.set()
        for pid in pids.values():
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
        app.shutdown()


def test_queued_solve_cannot_start_after_service_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = StructuralService(tmp_path)
    model = service.save(cantilever())
    jobs = JobManager(workers=1)
    occupied = threading.Event()
    release = threading.Event()
    calls: list[None] = []

    def occupy_worker() -> dict:
        occupied.set()
        release.wait(5)
        return {}

    monkeypatch.setattr(runner, "solve", lambda *args: calls.append(None))
    jobs.submit("occupied", occupy_worker)
    assert occupied.wait(5)
    queued = jobs.submit(
        "st_solve",
        lambda: service.solve(model["model_id"], 1, "vertical", "openseespy", threading.Event()),
    )
    try:
        service.close()
        release.set()
        wait_for(lambda: next(j for j in jobs.list() if j["job"] == queued)["state"] == "error")
        assert "shutting down" in next(j for j in jobs.list() if j["job"] == queued)["error"]
        assert not calls
        assert not list(service.folder(model["model_id"]).glob("run_*"))
    finally:
        release.set()
        jobs.shutdown()


def test_shutdown_timeout_is_bounded_and_does_not_claim_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = StructuralService(tmp_path)
    entered = threading.Event()
    release = threading.Event()
    stop = threading.Event()

    def stalled_preparation(*args: Any) -> dict:
        entered.set()
        release.wait(5)
        return {}

    monkeypatch.setattr(service, "_solve", stalled_preparation)
    worker = threading.Thread(target=lambda: service.solve("unused", 1, "x", "x", stop))
    worker.start()
    try:
        assert entered.wait(5)
        before = time.monotonic()
        with pytest.raises(StructuralError, match="cleanup timed out with 1"):
            service.close(timeout_s=0.05)
        assert time.monotonic() - before < 1
        assert stop.is_set()
        with pytest.raises(StructuralError, match="shutting down"):
            service.solve("unused", 1, "x", "x", threading.Event())
    finally:
        release.set()
        worker.join(2)
        assert not worker.is_alive()
        service.close()


def test_failed_or_precancelled_preparation_leaves_nothing_to_close(tmp_path: Path) -> None:
    service = StructuralService(tmp_path)
    with pytest.raises(StructuralError):
        service.solve("missing", 1, "x", "x", threading.Event())
    stopped = threading.Event()
    stopped.set()
    with pytest.raises(StructuralError, match="cancelled before preparation"):
        service.solve("missing", 1, "x", "x", stopped)
    service.close(timeout_s=0)
