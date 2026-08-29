"""The capture lane end to end on fakes (A42 T2 acceptance): ingest with
set manifests, reconstruction as a job with provenance, and every gate
refusing loudly with its fix — too few images, unknown set, bad detail,
no Docker for the drone lane, low disk, missing helper."""

from __future__ import annotations

import shutil
import time

import pytest
from fixtures_capture import write_dji_jpeg

from tee.app import TeeApp
from tee.capture import tools as capture_tools
from tee.capture.tools import register_capture_tools
from tee.extract.tools import register_extract_tools
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError

pytest.importorskip("PIL")

FAKE_HELPER = """#!/bin/sh
echo '{"event":"start","detail":"preview"}'
echo '{"event":"progress","fraction":0.5000}'
: > "$2"
printf '{"event":"model","path":"%s"}\\n' "$2"
echo '{"event":"done","seconds":0.2}'
"""

FAILING_HELPER = """#!/bin/sh
echo '{"event":"error","message":"session refused: not enough usable photos",\
"fix":"need >=10 sharp overlapping photos of one subject"}'
exit 3
"""


def _wait(app, job_id: str) -> dict:
    deadline = time.time() + 30
    while time.time() < deadline:
        status = app.jobs.status(job_id)
        if status["state"] in ("done", "error"):
            return status
        time.sleep(0.05)
    raise AssertionError(f"job never finished: {status}")


def _make_app(tmp_path, helper_script: str | None = FAKE_HELPER):
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    store, _registry = register_extract_tools(app, project)
    if helper_script is not None:
        helper = tmp_path / "fake-helper"
        helper.write_text(helper_script)
        helper.chmod(0o755)
        app.config.capture = {"helper": str(helper)}
    register_capture_tools(app, project, extract_store=store)
    return app


@pytest.fixture
def structure_set(tmp_path):
    return [
        write_dji_jpeg(tmp_path / f"room{i:02d}.jpg", "iPhone 17 Pro Max", make="Apple")
        for i in range(12)
    ]


def test_ingest_then_reconstruct_job_with_provenance(tmp_path, structure_set):
    app = _make_app(tmp_path)
    out = app.registry.call("capture_ingest", {"paths": [str(p) for p in structure_set]})
    assert out["files"] == 12 and not out["split_by_camera"]
    started = app.registry.call(
        "capture_reconstruct", {"set": out["set"], "engine": "photogrammetry"}
    )
    status = _wait(app, started["job"])
    assert status["state"] == "done", status
    result = status["result"]
    assert result["model"].endswith(f"{out['set']}_preview.usdz")
    assert result["provenance"]["engine"].startswith("PhotogrammetrySession")
    assert result["provenance"]["band"] == "meters-class absolute (consumer GNSS)"
    app.shutdown()


def test_helper_failure_reaches_the_job_as_its_own_error(tmp_path, structure_set):
    app = _make_app(tmp_path, helper_script=FAILING_HELPER)
    out = app.registry.call("capture_ingest", {"paths": [str(p) for p in structure_set]})
    started = app.registry.call(
        "capture_reconstruct", {"set": out["set"], "engine": "photogrammetry"}
    )
    status = _wait(app, started["job"])
    assert status["state"] == "error"
    assert "not enough usable photos" in status["error"]
    app.shutdown()


def test_gates_refuse_loudly(tmp_path, structure_set, monkeypatch):
    app = _make_app(tmp_path)
    few = app.registry.call("capture_ingest", {"paths": [str(p) for p in structure_set[:3]]})
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": few["set"], "engine": "photogrammetry"})
    assert excinfo.value.code == "capture_too_few_images"

    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": "nope"})
    assert excinfo.value.code == "capture_unknown_set"

    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": few["set"], "detail": "ultra"})
    assert excinfo.value.code == "capture_bad_detail"

    full = app.registry.call("capture_ingest", {"paths": [str(p) for p in structure_set]})
    usage = shutil.disk_usage(".")
    monkeypatch.setattr(
        capture_tools.shutil, "disk_usage", lambda _p: usage._replace(free=int(1e9))
    )
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": full["set"], "engine": "photogrammetry"})
    assert excinfo.value.code == "capture_disk_low"
    app.shutdown()


def test_drone_sets_route_to_odm_and_refuse_without_docker(tmp_path, monkeypatch):
    app = _make_app(tmp_path)
    drone = [
        write_dji_jpeg(tmp_path / f"d{i:02d}.jpg", "FC3582", RelativeAltitude="+60.0")
        for i in range(12)
    ]
    out = app.registry.call("capture_ingest", {"paths": [str(p) for p in drone]})
    monkeypatch.setattr(capture_tools.shutil, "which", lambda _n: None)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": out["set"]})  # engine auto
    assert excinfo.value.code == "capture_no_docker"
    assert "566 MB" in excinfo.value.fix

    monkeypatch.setattr(capture_tools.shutil, "which", lambda _n: "/usr/local/bin/docker")
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": out["set"]})
    assert excinfo.value.code == "capture_odm_pending"
    app.shutdown()


def test_missing_helper_names_the_make_fix(tmp_path, structure_set):
    app = _make_app(tmp_path, helper_script=None)
    app.config.capture = {}
    out = app.registry.call("capture_ingest", {"paths": [str(p) for p in structure_set]})
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": out["set"], "engine": "photogrammetry"})
    assert excinfo.value.code == "capture_helper_missing"
    assert "make" in excinfo.value.fix
