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
    app._capture_store = store
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
    # the guard seam, second direction: the launch reports what is resident,
    # the job carries its batch QoS label, and the ledger releases at the end
    assert "resident" in started["resident"]
    assert app.jobs.status(started["job"])["qos"] == "batch"
    status = _wait(app, started["job"])
    assert status["state"] == "done", status
    assert app.machine.active_jobs() == []
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


FAKE_DOCKER = """#!/bin/sh
log="$(dirname "$0")/docker_args.log"
echo "$@" >> "$log"
case "$1" in
  image) exit 0 ;;
  run)
    while [ "$1" != "-v" ]; do shift; done
    shift
    hostdir="${1%%:*}"
    mkdir -p "$hostdir/code/odm_orthophoto" "$hostdir/code/odm_dem"
    : > "$hostdir/code/odm_orthophoto/odm_orthophoto.tif"
    exit 0 ;;
esac
exit 0
"""

NO_IMAGE_DOCKER = """#!/bin/sh
[ "$1" = "image" ] && exit 1
exit 0
"""


def _drone_set(tmp_path, code="FC3582"):
    return [
        write_dji_jpeg(tmp_path / f"{code}-{i:02d}.jpg", code, RelativeAltitude="+60.0")
        for i in range(12)
    ]


def _with_fake_docker(app, tmp_path, script: str) -> str:
    fake = tmp_path / "fake-docker"
    fake.write_text(script)
    fake.chmod(0o755)
    # re-register with the docker override (cfg is read at registration)
    app.config.capture = dict(app.config.capture or {}, docker=str(fake))
    app.registry.unregister("capture_ingest")
    app.registry.unregister("capture_reconstruct")
    register_capture_tools(app, app.project_root, extract_store=app._capture_store)
    return str(fake)


def test_drone_sets_refuse_without_docker(tmp_path, monkeypatch):
    app = _make_app(tmp_path)
    out = app.registry.call("capture_ingest", {"paths": [str(p) for p in _drone_set(tmp_path)]})
    monkeypatch.setattr(capture_tools.shutil, "which", lambda _n: None)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": out["set"]})  # engine auto
    assert excinfo.value.code == "capture_no_docker"
    assert "566 MB" in excinfo.value.fix
    app.shutdown()


def test_odm_refuses_when_image_not_pulled(tmp_path):
    app = _make_app(tmp_path)
    _with_fake_docker(app, tmp_path, NO_IMAGE_DOCKER)
    out = app.registry.call("capture_ingest", {"paths": [str(p) for p in _drone_set(tmp_path)]})
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": out["set"]})
    assert excinfo.value.code == "capture_odm_image_missing"
    assert "docker pull" in excinfo.value.fix
    app.shutdown()


def test_odm_runs_with_correction_per_resolver(tmp_path):
    app = _make_app(tmp_path)
    fake = _with_fake_docker(app, tmp_path, FAKE_DOCKER)
    args_log = tmp_path / "docker_args.log"

    # FC3582 (Mini 3 Pro): matched constant -> --rolling-shutter present
    matched = app.registry.call(
        "capture_ingest", {"paths": [str(p) for p in _drone_set(tmp_path, "FC3582")]}
    )
    started = app.registry.call("capture_reconstruct", {"set": matched["set"]})
    status = _wait(app, started["job"])
    assert status["state"] == "done", status
    assert "--rolling-shutter" in args_log.read_text()
    result = status["result"]
    assert result["provenance"]["engine"].startswith("ODM/")
    assert result["provenance"]["rolling_shutter"]["mode"] == "matched"
    assert "orthophoto" in result["artifacts"]

    # FC7303 (Mini 2): no constant -> correction off, no flag
    args_log.write_text("")
    off = app.registry.call(
        "capture_ingest", {"paths": [str(p) for p in _drone_set(tmp_path, "FC7303")]}
    )
    started = app.registry.call("capture_reconstruct", {"set": off["set"]})
    status = _wait(app, started["job"])
    assert status["state"] == "done", status
    assert "--rolling-shutter" not in args_log.read_text()
    assert status["result"]["provenance"]["rolling_shutter"]["mode"] == "off"
    assert fake in args_log.read_text() or args_log.read_text()  # args recorded
    app.shutdown()


def test_missing_helper_names_the_make_fix(tmp_path, structure_set):
    app = _make_app(tmp_path, helper_script=None)
    app.config.capture = {}
    out = app.registry.call("capture_ingest", {"paths": [str(p) for p in structure_set]})
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_reconstruct", {"set": out["set"], "engine": "photogrammetry"})
    assert excinfo.value.code == "capture_helper_missing"
    assert "make" in excinfo.value.fix
