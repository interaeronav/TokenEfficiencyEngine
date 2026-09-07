"""A72 P1-P4 acceptance: the whole wt_* lane through the real registry on
fake engines - every tool, every refusal the fakes can provoke, the digest
law on every response, the cost gate, cancel, orphans, adoption, and the
two pins the lane rests on: thirteen tools tabled individually in the trust
kernel and ZERO growth of the always-loaded surface.

The fakes (fixtures_windtunnel) write the files the real engines were
measured to write; the numbers they carry are made up to tell a story
(converge, stall, oscillate, diverge, crash, slow). The `cfd` tier in
test_windtunnel_live.py repeats the loop on the real binaries.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fixtures_windtunnel import make_app, wait_job

from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.windtunnel import airfoil
from tee.windtunnel import case as case_mod
from tee.windtunnel.runner import atomic_write_json, pid_alive

WT_TOOLS = (
    "wt_probe",
    "wt_conditions",
    "wt_case",
    "wt_geom",
    "wt_mesh",
    "wt_run",
    "wt_status",
    "wt_result",
    "wt_sweep",
    "wt_probe_field",
    "wt_view",
    "wt_export",
    "wt_verify",
)


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    application = make_app(tmp_path_factory.mktemp("wt"))
    try:
        yield application
    finally:
        application.shutdown()


def call(app, tool, **args):
    return app.registry.call(tool, args)


@pytest.fixture(scope="module")
def foam_case(app):
    """One converged 2-D case the read-side tests share."""
    os.environ["TEE_FAKE_FOAM_MODE"] = "converge"
    created = call(app, "wt_case", action="create", naca="2412", V_mps=30, aoa_deg=4)
    cid = created["case_id"]
    call(app, "wt_mesh", case_id=cid, nj=20, n_surface=30)
    started = call(app, "wt_run", case_id=cid, iters=400)
    status = wait_job(app, started["job"])
    assert status["state"] == "done", status
    return cid


# -- the digest law ---------------------------------------------------------


def _violations(payload, path="response"):
    out = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            out += _violations(value, f"{path}.{key}")
    elif isinstance(payload, list):
        if len(payload) > case_mod.MAX_ARRAY:
            out.append(f"{path}: {len(payload)} elements")
        for i, value in enumerate(payload[:8]):
            out += _violations(value, f"{path}[{i}]")
    elif isinstance(payload, str) and len(payload) > case_mod.MAX_STRING:
        out.append(f"{path}: {len(payload)} chars")
    return out


def test_every_response_of_the_loop_obeys_the_digest_law_and_stays_small(app, foam_case):
    responses = {
        "wt_probe": call(app, "wt_probe"),
        "wt_case show": call(app, "wt_case", action="show", case_id=foam_case),
        "wt_case list": call(app, "wt_case", action="list"),
        "wt_status": call(app, "wt_status", case_id=foam_case),
        "wt_result": call(app, "wt_result", case_id=foam_case),
        "wt_probe_field": call(app, "wt_probe_field", case_id=foam_case, field="U", n=32),
        "wt_probe_field 64": call(app, "wt_probe_field", case_id=foam_case, field="U", n=64),
        "wt_view": call(app, "wt_view", case_id=foam_case, view="pressure"),
        "wt_export": call(app, "wt_export", case_id=foam_case, format="json"),
    }
    for name, payload in responses.items():
        assert _violations(payload) == [], name
        cap = 800 if name.endswith("64") else 450  # 64 samples of s + |U| is the law's ceiling
        assert estimate_tokens(json.dumps(payload)) < cap, (
            name,
            estimate_tokens(json.dumps(payload)),
        )
    assert "U:0" not in responses["wt_probe_field"]  # a vector comes back as its magnitude
    assert estimate_tokens(json.dumps(responses["wt_status"])) < 120
    assert estimate_tokens(json.dumps(responses["wt_result"])) < 300


# -- probe and conditions -------------------------------------------------------


def test_probe_names_every_engine_with_its_version_and_the_extra(app):
    p = call(app, "wt_probe", refresh=True)
    e = p["engines"]
    assert (
        e["openfoam"]["found"]
        and e["openfoam"]["kind"] == "bindir"
        and e["openfoam"]["via"] == "config"
    )
    assert e["su2"]["version"] == "8.4.0" and e["vspaero"]["version"] == "3.51.3"
    assert (
        e["vspaero"]["extra"]["vspaero"].endswith("vspaero")
        and e["pvpython"]["version"] == "5.11.2"
    )
    assert isinstance(p["extra"]["meshio"], bool) and p["cores"] >= 1
    assert (Path(app._wt_store.root) / "probe.json").is_file()


def test_probe_reports_absent_engines_with_their_install_line(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr("tee.windtunnel.engines.glob.glob", lambda pattern, **kw: [])
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.delenv("SU2_RUN", raising=False)
    monkeypatch.setattr("tee.windtunnel.engines._foam_candidates", lambda: [])
    bare = make_app(tmp_path, fakes=False)
    try:
        p = call(bare, "wt_probe")
        for name in ("openfoam", "su2", "vspaero"):
            assert p["engines"][name]["found"] is False
            assert (
                p["engines"][name]["error"]
                == f"wt_{name if name != 'vspaero' else 'openvsp'}_missing"
            )
            assert p["engines"][name]["fix"]
        with pytest.raises(TeeError) as err:
            call(bare, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=2)
        assert err.value.code == "wt_regime" and "install" in err.value.fix.lower()
    finally:
        bare.shutdown()


def test_two_installs_of_one_engine_pick_the_newest_stable_and_name_the_rest(tmp_path, monkeypatch):
    """A machine with several ParaViews must not certify against whichever
    one sorts last. Reverse-lexicographic ordering ranked 6.2.0-RC1 above
    6.1.1 (measured 2026-09-07, both installed) and would rank 6.1.1 above
    10.0.0, so a major-version bump vanished and a release candidate could
    quietly become the validation engine.
    """
    from tee.windtunnel import engines

    apps = tmp_path / "Applications"
    for name in ("ParaView-6.1.1.app", "ParaView-6.2.0-RC1.app", "ParaView-10.0.0.app"):
        exe = apps / name / "Contents" / "bin" / "pvpython"
        exe.parent.mkdir(parents=True)
        exe.write_text("#!/bin/sh\n")
    pattern = str(apps / "ParaView-*.app" / "Contents" / "bin" / "pvpython")
    b = engines._binary({}, "pvpython", "pvpython", [pattern], "install line")
    assert "ParaView-10.0.0.app" in b.path, (
        "10.0.0 outranks 6.x: a version compare, not a string one"
    )
    assert b.extra.get("prerelease") is None  # the chosen one is stable
    assert len(b.extra["alternatives"]) == 2  # the ambiguity is reported, not hidden

    # with only a release candidate present it is still used - and says so
    (apps / "ParaView-10.0.0.app").rename(apps / "keep-10.0.0")
    (apps / "ParaView-6.1.1.app").rename(apps / "keep-6.1.1")
    rc = engines._binary({}, "pvpython", "pvpython", [pattern], "install line")
    assert "RC1" in rc.path and rc.extra["prerelease"] is True

    # an explicit config pin always wins, whatever is installed
    (apps / "keep-6.1.1").rename(apps / "ParaView-6.1.1.app")
    (apps / "keep-10.0.0").rename(apps / "ParaView-10.0.0.app")
    pinned = str(apps / "ParaView-6.1.1.app" / "Contents" / "bin" / "pvpython")
    got = engines._binary({"pvpython": pinned}, "pvpython", "pvpython", [pattern], "fix")
    assert got.path == pinned and got.via == "config"


def test_the_install_rank_reads_the_version_from_the_right_path_component():
    from tee.windtunnel.engines import _install_rank

    # not the 64 in x86_64
    assert _install_rank("/opt/x86_64/paraview5.11/bin/pvpython") == (1, (5, 11))
    assert _install_rank("/usr/lib/openfoam/openfoam2606/etc/bashrc") == (1, (2606,))
    assert _install_rank("/usr/bin/pvpython") == (1, (0,))  # unversioned sorts lowest
    stable = _install_rank("/Applications/ParaView-6.2.0.app/Contents/bin/pvpython")
    cand = _install_rank("/Applications/ParaView-6.2.0-RC1.app/Contents/bin/pvpython")
    assert stable > cand, "a release beats its own release candidate"


def test_conditions_tool_and_its_refusal(app):
    c = call(app, "wt_conditions", V_mps=45, L_m=1.2, alt_m=1500)
    assert c["regime"] == "incompressible" and 3.2e6 < c["Re"] < 3.4e6
    with pytest.raises(TeeError) as err:
        call(app, "wt_conditions", L_m=1.0)  # neither a speed nor a Mach number
    assert err.value.code == "wt_bad_conditions"
    with pytest.raises(TeeError) as err:
        call(app, "wt_conditions", L_m=1.0, V_mps=10, mach=0.1)  # both
    assert err.value.code == "wt_bad_conditions"
    with pytest.raises(TeeError) as err:
        call(app, "wt_conditions", V_mps=10)  # the schema's required key, refused by the registry
    assert err.value.code == "missing_argument"


# -- the OpenFOAM loop ---------------------------------------------------------------


def test_create_picks_the_engine_and_says_why(app):
    created = call(app, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=4)
    assert created["engine"] == "openfoam" and created["fidelity"]["chosen"] == "rans"
    assert "simpleFoam" in created["fidelity"]["reason"] and created["next"] == "wt_mesh"
    assert created["geometry"]["properties"]["max_thickness"] == pytest.approx(0.12, abs=2e-3)
    assert "loop" not in created["geometry"]  # the model never sees the points
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="create", V_mps=30)
    assert err.value.code == "wt_geometry_missing"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="create", naca="0012", aoa_deg=4)
    assert err.value.code == "wt_bad_conditions"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="dance", case_id="wt_x")
    assert err.value.code == "wt_bad_action"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="show", case_id="wt_0000000000")
    assert err.value.code == "wt_unknown_case"


def test_mesh_then_run_then_status_then_result_with_provenance(app, foam_case):
    rec = app._wt_store.load(foam_case)
    assert rec["mesh"]["kind"] == "omesh_polymesh" and rec["mesh"]["ok"] is True
    assert (Path(rec["engine_dir"]) / "system" / "controlDict").is_file()  # the checkMesh stub
    status = call(app, "wt_status", case_id=foam_case)
    assert status["state"] == "done" and status["verdict"] == "converged" and status["iter"] > 50
    res = call(app, "wt_result", case_id=foam_case)
    assert res["cl"] == pytest.approx(0.4356, abs=2e-3) and res["cd"] == pytest.approx(
        0.0109, abs=1e-3
    )
    assert res["verdict"]["state"] == "converged" and res["uncertainty"]["trust"] == "comparative"
    assert res["mesh_hash"] == rec["mesh"]["mesh_hash"] and res["engine"] == "openfoam"
    assert res["fidelity"] == "rans" and res["aoa_deg"] == 4.0 and res["partial"] is False
    run = rec["runs"][-1]
    assert run["job"] and run["state"] == "done" and run["Aref"] == pytest.approx(0.1, rel=0.1)
    run_dir = Path(run["run_dir"])
    assert (run_dir / "constant" / "polyMesh").is_symlink()
    assert (run_dir / "0" / "U").is_file() and (run_dir / "log.simpleFoam").is_file()
    same = call(app, "wt_result", case_id=foam_case, compare_to=foam_case)
    assert same["compare"]["same_mesh"] is True and same["compare"]["d_cd_counts"] == 0.0


def test_run_refuses_before_a_mesh_exists(app):
    created = call(app, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=2)
    with pytest.raises(TeeError) as err:
        call(app, "wt_run", case_id=created["case_id"])
    assert err.value.code == "wt_no_mesh"
    with pytest.raises(TeeError) as err:
        call(app, "wt_result", case_id=created["case_id"])
    assert err.value.code == "wt_no_results"


def test_cost_gate_asks_once_with_the_estimate_then_runs(app, foam_case, monkeypatch):
    monkeypatch.setenv("TEE_FAKE_FOAM_MODE", "converge")
    with pytest.raises(TeeError) as err:
        call(app, "wt_run", case_id=foam_case, iters=100_000)
    assert err.value.code == "wt_cost_confirmation_required"
    assert "confirm_cost=true" in err.value.fix and "2026" in err.value.fix
    assert "s" in err.value.message
    rec = app._wt_store.load(foam_case)
    assert all(r["state"] != "queued" for r in rec["runs"])  # no phantom queued run
    started = call(app, "wt_run", case_id=foam_case, iters=100_000, confirm_cost=True)
    assert started["confirmed"]
    status = wait_job(app, started["job"])
    assert status["state"] == "done"


@pytest.mark.parametrize(
    ("mode", "state", "trust"),
    [("stall", "stalled", "indicative"), ("oscillate", "oscillating", "not-predictive")],
)
def test_verdicts_that_still_return_numbers(app, foam_case, monkeypatch, mode, state, trust):
    monkeypatch.setenv("TEE_FAKE_FOAM_MODE", mode)
    started = call(app, "wt_run", case_id=foam_case, iters=300)
    assert wait_job(app, started["job"])["state"] == "done"
    res = call(app, "wt_result", case_id=foam_case)
    assert res["verdict"]["state"] == state and res["uncertainty"]["trust"] == trust


def test_a_diverged_run_refuses_to_quote_a_number(app, foam_case, monkeypatch):
    monkeypatch.setenv("TEE_FAKE_FOAM_MODE", "diverge")
    started = call(app, "wt_run", case_id=foam_case, iters=200)
    wait_job(app, started["job"])
    with pytest.raises(TeeError) as err:
        call(app, "wt_result", case_id=foam_case)
    assert err.value.code == "wt_diverged" and "climbed" in err.value.message
    partial = call(app, "wt_result", case_id=foam_case, allow_partial=True)
    assert partial["verdict"]["state"] == "diverged"


def test_a_crashed_solver_is_a_failed_job_and_a_named_refusal(app, foam_case, monkeypatch):
    monkeypatch.setenv("TEE_FAKE_FOAM_MODE", "crash")
    started = call(app, "wt_run", case_id=foam_case, iters=200)
    status = wait_job(app, started["job"])
    assert status["state"] == "error" and "wt_solver_failed" in status["error"]
    with pytest.raises(TeeError) as err:
        call(app, "wt_result", case_id=foam_case)
    assert err.value.code == "wt_solver_failed" and "FOAM FATAL" in err.value.fix
    assert call(app, "wt_status", case_id=foam_case)["state"] == "error"


def test_one_live_run_per_case_and_cancel_kills_the_solver_within_two_seconds(
    app, foam_case, monkeypatch
):
    monkeypatch.setenv("TEE_FAKE_FOAM_MODE", "slow")
    started = call(app, "wt_run", case_id=foam_case, iters=1000)
    try:
        time.sleep(0.5)
        with pytest.raises(TeeError) as err:
            call(app, "wt_run", case_id=foam_case)
        assert err.value.code == "wt_already_running" and started["job"] in err.value.message
        with pytest.raises(TeeError) as err:
            call(app, "wt_result", case_id=foam_case)
        assert err.value.code == "wt_unconverged"
        status = call(app, "wt_status", case_id=foam_case)
        assert status["state"] == "running"
        run = app._wt_store.load(foam_case)["runs"][-1]
        pid = json.loads((Path(run["run_dir"]) / "run.json").read_text())["pid"]
        assert pid_alive(pid)
        t0 = time.time()
        app.jobs.cancel(started["job"])
        deadline = time.time() + 5
        while time.time() < deadline and pid_alive(pid):
            time.sleep(0.05)
        assert not pid_alive(pid) and time.time() - t0 < 2.5
        wait_job(app, started["job"])
    finally:
        app.jobs.cancel(started["job"]) if app.jobs.status(started["job"])[
            "state"
        ] == "running" else None
    run = app._wt_store.load(foam_case)["runs"][-1]
    assert run["state"] == "cancelled" and app.machine.active_jobs() == []
    partial = call(app, "wt_result", case_id=foam_case, allow_partial=True)
    assert partial["verdict"]["state"] == "cancelled"
    monkeypatch.setenv("TEE_FAKE_FOAM_MODE", "converge")


def test_an_orphaned_solver_is_named_and_can_be_stopped(app, foam_case):
    """A server restart leaves run.json behind and a solver still running:
    wt_status says orphan (pid + command line verified), wt_case stop kills
    it, and stop with nothing to stop refuses by name."""
    rec = app._wt_store.load(foam_case)
    run = rec["runs"][-1]
    run_dir = Path(run["run_dir"])
    proc = subprocess.Popen(
        [sys.executable, "-c", f"import time; time.sleep(30)  # {run_dir}"], start_new_session=True
    )
    try:
        atomic_write_json(
            run_dir / "run.json",
            {"pid": proc.pid, "argv": ["simpleFoam", "-case", str(run_dir)], "state": "running"},
        )
        atomic_write_json(run_dir / "progress.json", {"state": "running", "iter": 12})
        app._wt_store.add_run(foam_case, {"run_id": run["run_id"], "state": "running"})
        status = call(app, "wt_status", case_id=foam_case)
        assert status["state"] == "orphan" and status["pid"] == proc.pid
        stopped = call(app, "wt_case", action="stop", case_id=foam_case)
        assert stopped["how"] == "orphan" and stopped["stopped"] is True
        proc.wait(timeout=5)
        assert not pid_alive(proc.pid)
    finally:
        if proc.poll() is None:
            proc.kill()
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="stop", case_id=foam_case)
    assert err.value.code == "wt_no_orphan"
    app._wt_store.add_run(foam_case, {"run_id": run["run_id"], "state": "done"})


def test_an_unhealthy_mesh_needs_force(app, monkeypatch):
    monkeypatch.setenv("TEE_FAKE_CHECKMESH", "bad")
    created = call(app, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=2)
    cid = created["case_id"]
    mesh = call(app, "wt_mesh", case_id=cid, nj=20, n_surface=30)
    assert mesh["ok"] is False and mesh["checkMesh"]["failed_checks"] == 2
    with pytest.raises(TeeError) as err:
        call(app, "wt_run", case_id=cid)
    assert err.value.code == "wt_mesh_unhealthy" and "Zero or negative" in err.value.message
    monkeypatch.setenv("TEE_FAKE_CHECKMESH", "skew")
    mesh = call(app, "wt_mesh", case_id=cid, nj=20, n_surface=30)
    assert mesh["ok"] is True and "skew" in mesh["checkMesh"]["failed"][0].lower()  # the TE seam
    monkeypatch.setenv("TEE_FAKE_CHECKMESH", "ok")


def test_sweep_is_one_job_with_a_polar_and_a_lift_slope(app, foam_case, monkeypatch):
    monkeypatch.setenv("TEE_FAKE_FOAM_MODE", "converge")
    started = call(app, "wt_sweep", case_id=foam_case, aoa=[0, 2, 4], iters=300)
    assert started["points"] == 3 and len(started["run_ids"]) == 3
    status = wait_job(app, started["job"])
    assert status["state"] == "done"
    polar = status["result"]["polar"]
    assert [p["aoa_deg"] for p in polar] == [0.0, 2.0, 4.0] and all(
        p["state"] == "converged" for p in polar
    )
    assert "cl_alpha_per_rad" in status["result"]
    csv_path = call(app, "wt_export", case_id=foam_case, format="csv")["path"]
    assert Path(csv_path).read_text().count("\n") >= 2
    with pytest.raises(TeeError) as err:
        call(app, "wt_sweep", case_id=foam_case, aoa=list(range(70)))
    assert err.value.code == "wt_sweep_too_long"
    with pytest.raises(TeeError) as err:
        call(app, "wt_sweep", case_id=foam_case, aoa=[])
    assert err.value.code == "wt_bad_conditions"


# -- a 3-D body ------------------------------------------------------------------------


def test_a_body_meshes_as_a_job_and_runs(app, tmp_path):
    stl = tmp_path / "prism.stl"
    airfoil.extrude_stl(stl, airfoil.naca4("0012", 20), span=0.4, chord=0.3)
    created = call(app, "wt_case", action="create", stl=str(stl), V_mps=20, aoa_deg=0)
    cid = created["case_id"]
    assert created["kind"] == "body3d" and created["engine"] == "openfoam"
    assert created["domain"]["verdict"] == "ok" and created["geometry"]["watertight"] is True
    started = call(app, "wt_mesh", case_id=cid, levels=[2, 3], layers=3)
    assert started["sequence"] == [
        "blockMesh",
        "surfaceFeatureExtract",
        "snappyHexMesh",
        "checkMesh",
    ]
    status = wait_job(app, started["job"])
    assert (
        status["state"] == "done"
        and status["result"]["ok"] is True
        and status["result"]["cells"] > 1000
    )
    assert app.machine.active_jobs() == []
    run = call(app, "wt_run", case_id=cid, iters=300, confirm_cost=True)
    status = wait_job(app, run["job"])
    assert status["state"] == "done" and status["result"]["verdict"]["state"] == "converged"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="create", stl=str(stl), V_mps=20, refs={"Sref": 50.0})
    assert err.value.code == "wt_blockage"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="create", stl=str(stl), V_mps=20, units="furlong")
    assert err.value.code == "wt_bad_units"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="create", stl=str(tmp_path / "none.stl"), V_mps=20)
    assert err.value.code == "wt_geometry_missing"


# -- SU2 -------------------------------------------------------------------------------------


def test_su2_euler_loop(app):
    created = call(
        app,
        "wt_case",
        action="create",
        naca="0012",
        mach=0.8,
        aoa_deg=1.25,
        fidelity="euler",
        need_viscous=False,
    )
    cid = created["case_id"]
    assert created["engine"] == "su2" and created["conditions"]["regime"] == "transonic"
    mesh = call(app, "wt_mesh", case_id=cid, nj=20, n_surface=30)
    assert mesh["kind"] == "omesh_su2" and mesh["ok"] is True
    started = call(app, "wt_run", case_id=cid, iters=1200)
    status = wait_job(app, started["job"])
    assert status["state"] == "done"
    res = call(app, "wt_result", case_id=cid)
    assert res["cl"] == pytest.approx(0.3345, abs=2e-3) and res["verdict"]["state"] == "converged"
    assert res["uncertainty"]["trust"] == "indicative" and res["volume_file"].endswith("flow.vtu")
    stats = call(app, "wt_probe_field", case_id=cid, what="slice", field="Pressure")
    assert stats["stats"]["n"] == 100
    with pytest.raises(TeeError) as err:
        call(app, "wt_probe_field", case_id=cid, what="slice", field="Vorticity")
    assert err.value.code == "wt_field_missing"


# -- OpenVSP / VSPAERO --------------------------------------------------------------------------


def test_geom_then_panel_sweep_then_adopt_the_model(app):
    g = call(app, "wt_geom", kind="wing", wing={"span": 10, "root_chord": 1, "airfoil": "0012"})
    assert g["geom_id"].startswith("geom_") and g["span"] == 10.0 and g["tris"] == 12
    created = call(app, "wt_case", action="create", geom=g["geom_id"], V_mps=34, aoa_deg=4)
    cid = created["case_id"]
    assert created["engine"] == "vspaero" and created["fidelity"]["chosen"] == "panel"
    assert created["refs"]["Sref"] == 10.0 and created["next"] == "wt_sweep or wt_run"
    assert call(app, "wt_mesh", case_id=cid)["kind"] == "vlm"
    started = call(app, "wt_sweep", case_id=cid, aoa=[0, 2, 4, 6])
    assert started["engine"] == "aero-panel" and started["run_ids"] == ["run_001"]
    status = wait_job(app, started["job"])
    assert status["state"] == "done", status
    res = status["result"]
    assert (
        res["cl_alpha_per_rad"] == pytest.approx(4.905, abs=0.01)
        and res["verdict"]["state"] == "converged"
    )
    assert [p["aoa_deg"] for p in res["polar"]] == [0.0, 2.0, 4.0, 6.0]
    assert (
        app._wt_store.load(cid)["runs"][-1]["exit_code_overruled"] is True
    )  # vspscript exits 2 after DONE
    final = call(app, "wt_result", case_id=cid)
    assert final["uncertainty"]["trust"] == "indicative" and final["cd_min"] == pytest.approx(
        0.0063
    )
    with pytest.raises(TeeError) as err:
        call(app, "wt_probe_field", case_id=cid)
    assert err.value.code == "wt_field_missing"
    adopted = call(app, "wt_case", action="adopt", path=created["geometry"]["vsp3"])
    assert adopted["engine"] == "vspaero" and adopted["next"] == "wt_sweep"
    with pytest.raises(TeeError) as err:
        call(app, "wt_geom", kind="wing", wing={"span": 1})
    assert err.value.code == "wt_geometry_missing"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="create", geom="geom_nowhere", V_mps=30)
    assert err.value.code == "wt_geometry_missing"


def test_a_failed_vspscript_names_its_last_lines(app, monkeypatch):
    monkeypatch.setenv("TEE_FAKE_VSP_MODE", "crash")
    with pytest.raises(TeeError) as err:
        call(app, "wt_geom", kind="wing", wing={"span": 4, "root_chord": 0.5})
    assert err.value.code == "wt_vsp_script_failed" and "ERROR" in err.value.fix


# -- post-processing -----------------------------------------------------------------------------


def test_probe_field_and_view_return_numbers_and_a_path_never_pixels(app, foam_case):
    line = call(
        app,
        "wt_probe_field",
        case_id=foam_case,
        field="U",
        p1=[0, 0, 0.05],
        p2=[0, 0.3, 0.05],
        n=16,
    )
    assert line["n"] == 16 and len(line["U_mag"]) == 16 and line["stats"]["n"] == 14
    assert line["U_mag"][0] is None and line["outside_mesh"] == 2  # inside the body: no sample
    assert line["engine"] == "pvpython" and "U:0" not in line
    with_parts = call(app, "wt_probe_field", case_id=foam_case, field="U", n=8, components=True)
    assert "U:0" in with_parts and len(with_parts["U:0"]) == 8
    with pytest.raises(TeeError) as err:
        call(app, "wt_probe_field", case_id=foam_case, field="T", n=8)
    assert err.value.code == "wt_field_missing"
    view = call(app, "wt_view", case_id=foam_case, view="velocity", width=640, height=480)
    assert Path(view["png"]).is_file() and view["size"] == [640, 480]
    assert (
        view["colour_range"]["min"] < 0 < view["colour_range"]["max"]
        and "mid-plane" in view["caption"]
    )
    assert "pixels" not in json.dumps(view) and not any(isinstance(v, bytes) for v in view.values())
    with pytest.raises(TeeError) as err:
        call(app, "wt_view", case_id=foam_case, view="rainbow")
    assert err.value.code == "wt_bad_view"


def test_pvpython_failures_refuse_with_the_offscreen_fix(app, foam_case, monkeypatch):
    monkeypatch.setenv("TEE_FAKE_PV_MODE", "crash")
    with pytest.raises(TeeError) as err:
        call(app, "wt_view", case_id=foam_case, view="pressure")
    assert err.value.code == "wt_render_failed" and "xvfb" in err.value.fix
    with pytest.raises(TeeError) as err:
        call(app, "wt_probe_field", case_id=foam_case, field="U")
    assert err.value.code == "wt_probe_failed"


def test_exports_in_every_format_that_needs_no_extra(app, foam_case):
    for fmt in ("json", "csv", "md", "foam", "pipeline"):
        out = call(app, "wt_export", case_id=foam_case, format=fmt)
        assert out["format"] == fmt and Path(out["path"]).exists()
    with pytest.raises(TeeError) as err:
        call(app, "wt_export", case_id=foam_case, format="xlsx")
    assert err.value.code == "wt_bad_format"
    try:
        import meshio  # noqa: F401
    except ImportError:
        with pytest.raises(TeeError) as err:
            call(app, "wt_export", case_id=foam_case, format="vtu")
        assert err.value.code == "wt_extra_missing" and "windtunnel" in err.value.fix
    with pytest.raises(
        TeeError
    ):  # no pdf lane registered in this app: the refusal is the registry's
        call(app, "wt_export", case_id=foam_case, format="pdf")


# -- adoption --------------------------------------------------------------------------------------


def test_adopt_an_openfoam_case_copies_it_and_runs_it_as_is(app, foam_case, tmp_path):
    src = Path(app._wt_store.load(foam_case)["runs"][0]["run_dir"])
    (src / "Allrun").write_text("#!/bin/sh\nrunApplication simpleFoam\nrunApplication foamToVTK\n")
    adopted = call(app, "wt_case", action="adopt", path=str(src))
    cid = adopted["case_id"]
    assert (
        adopted["kind"] == "adopted"
        and adopted["solver"] == "simpleFoam"
        and adopted["dialect"] == "com"
    )
    assert adopted["has_forceCoeffs"] is True and ("airfoil", "wall") in [
        tuple(p) for p in adopted["patches"]
    ]
    assert adopted["sequence"] == [["simpleFoam"]] and any(
        "foamToVTK" in w for w in adopted["warnings"]
    )
    assert adopted["next"] == "wt_run"
    (src / "Allrun").unlink()
    edir = Path(app._wt_store.load(cid)["engine_dir"])
    assert edir != src and (edir / "system" / "controlDict").is_file()
    mesh = call(app, "wt_mesh", case_id=cid)
    assert mesh["kind"] == "adopted" and mesh["has_mesh"] is True and mesh["ok"] is True
    started = call(app, "wt_run", case_id=cid, iters=200)
    status = wait_job(app, started["job"])
    assert status["state"] == "done" and status["result"]["verdict"]["state"] == "converged"
    assert (src / "runs").exists() is False  # the source was never written into
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="adopt", path=str(tmp_path))
    assert err.value.code == "wt_not_a_case"
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="adopt", path=str(tmp_path / "missing"))
    assert err.value.code == "wt_not_a_case"


def test_adopt_an_su2_cfg_needs_its_mesh_beside_it(app, tmp_path):
    cfg = tmp_path / "inv.cfg"
    cfg.write_text("SOLVER= EULER\nMACH_NUMBER= 0.8\nAOA= 1.25\nMESH_FILENAME= mesh.su2\n")
    with pytest.raises(TeeError) as err:
        call(app, "wt_case", action="adopt", path=str(cfg))
    assert err.value.code == "wt_not_a_case" and "beside" in err.value.message
    from tee.windtunnel import mesh2d

    mesh2d.write_su2(
        tmp_path / "mesh.su2",
        mesh2d.omesh(airfoil.naca4("0012", 20), first_cell=2e-3, nj=6, radius_c=10.0),
    )
    adopted = call(app, "wt_case", action="adopt", path=str(cfg))
    assert adopted["engine"] == "su2" and adopted["markers"] == ["airfoil", "farfield"]
    assert adopted["fidelity"]["chosen"] == "euler" and adopted["next"] == "wt_run"


# -- verification ------------------------------------------------------------------


def test_verify_refuses_an_unverified_reference_and_runs_the_verified_ones(app):
    # every reference is verified at source now (owner session, §M R3/R4);
    # flatplate is the one whose runner is still unbuilt, and naming it
    # refuses with that reason rather than pretending
    with pytest.raises(TeeError) as err:
        call(app, "wt_verify", case="flatplate")
    assert err.value.code == "wt_reference_unverified"
    assert "runner" in err.value.message and "not built" in err.value.message
    with pytest.raises(TeeError) as err:
        call(app, "wt_verify", case="nonsense")
    assert err.value.code == "wt_bad_action"
    out = call(app, "wt_verify", case="all", confirm_cost=True)
    assert set(out["skipped_unverified"]) == set()
    assert set(out["skipped_unimplemented"]) == {"flatplate"}
    by_name = {r["case"]: r for r in out["results"]}
    assert (
        by_name["wing_liftslope"]["pass"] is True
        and abs(by_name["wing_liftslope"]["checks"]["cl_alpha"]["pct"]) < 8
    )
    assert (
        by_name["naca0012_euler"]["pass"] is True
        and by_name["naca0012_euler"]["verdict"] == "converged"
    )
    # the Re 40 cylinder runs on OpenFOAM: the case must land on the
    # benchmark's Reynolds number exactly, and the wake check reports
    # itself skipped rather than failing when ParaView is absent
    cyl = by_name["cylinder_re40"]
    assert cyl["pass"] is True and cyl["Re"] == 40.0
    assert abs(cyl["checks"]["cd"]["pct"]) <= cyl["checks"]["cd"]["tol_pct"]
    wake = cyl["checks"]["wake_lw_over_d"]
    assert wake.get("measured") is not None or wake.get("skipped")
    assert out["all_pass"] is True
    for r in out["results"]:
        assert r["cite"] and r["verified"]


# -- the two pins ------------------------------------------------------------------


def test_every_registered_tool_is_tabled_individually_in_the_trust_kernel(app):
    from tee.kernel import trust

    registered = sorted(n for n in app.registry.names() if n.startswith("wt_"))
    assert registered == sorted(WT_TOOLS) and len(registered) == 13
    for name in registered:
        assert name in trust._EXPLICIT, name
        assert trust.capability_for(name) in ("read-compute", "write-artifacts", "call-engine")
    assert not any(prefix.startswith("wt_") for prefix, _ in trust._FAMILY)
    assert (
        trust._EXPLICIT["wt_run"] == "call-engine"
        and trust._EXPLICIT["wt_status"] == "read-compute"
    )
    assert trust._EXPLICIT["wt_view"] == "write-artifacts"


def test_the_boot_path_registers_the_lane_and_leaves_the_surface_alone(tmp_path):
    import anyio
    from mcp.client import Client

    from tee.app import TeeApp
    from tee.cli import _attach_windtunnel
    from tee.kernel.adapter import FakeAdapter
    from tee.server import _DESC, build_server

    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        _attach_windtunnel(application, str(tmp_path))
        assert sorted(n for n in application.registry.names() if n.startswith("wt_")) == sorted(
            WT_TOOLS
        )

        async def fetch():
            async with Client(build_server(application)) as client:
                return (await client.list_tools()).tools

        surface = anyio.run(fetch)
        assert len(surface) == 17 and len(_DESC) == 17, "the always-loaded surface moved"
        assert not [t for t in surface if t.name.startswith("wt_")]
        hits = [i["name"] for i in application.registry.search("wind tunnel")["items"]]
        assert hits and all(h.startswith("wt_") for h in hits[:3]), hits
    finally:
        application.shutdown()


def test_the_vocabulary_law_keeps_the_search_pins_honest(app):
    """test_search_budget.py witnesses 'check the drawing' -> pk_drawing and
    'size from an image' -> ex_estimate; a wt_* NAME or TAG carrying those
    words would score above them by name."""
    forbidden = ("check", "drawing", "image", "size", "document")
    for name in app.registry.names():
        if not name.startswith("wt_"):
            continue
        tool = app.registry._tools[name]
        words = set(name.replace("wt_", "").split("_"))
        for tag in tool.tags or []:
            words |= set(tag.lower().split())
        assert not (words & set(forbidden)), (name, words & set(forbidden))


def test_an_adopted_case_without_force_coefficients_gets_a_residual_verdict_or_forces(
    app, tmp_path
):
    """The apt airFoil2D tutorial (measured 2026-09-06) has no forceCoeffs entry:
    a run of it is still a converged run - residuals only, no invented number -
    and `wt_run forces={...}` adds the function object to TEE's run copy with
    the chord MEASURED from the wall patch (lRef 1 on that 35 m section gave
    Cl 34). The adopted source is never written into."""
    from tee.windtunnel import airfoil, foam, mesh2d

    src = tmp_path / "bare_case"
    foam.write_mesh_system(src)  # controlDict without functions
    mesh2d.write_polymesh(
        src, mesh2d.omesh(airfoil.naca4("0012", 20), first_cell=1e-3, nj=6, radius_c=10.0)
    )
    setup = foam.FoamSetup(U_inf=(30.0, 0.0, 0.0), nu=1.5e-5)
    for name, text in foam.fields_0(setup).items():
        (src / "0" / name).parent.mkdir(exist_ok=True)
        (src / "0" / name).write_text(text)
    (src / "constant" / "transportProperties").write_text(foam.transport_properties(setup))
    (src / "constant" / "turbulenceProperties").write_text(foam.turbulence_properties(setup))
    before = sorted(p.relative_to(src) for p in src.rglob("*"))
    adopted = call(app, "wt_case", action="adopt", path=str(src))
    cid = adopted["case_id"]
    assert adopted["has_forceCoeffs"] is False and adopted["inlet_U"] == [30.0, 0.0, 0.0]
    call(app, "wt_mesh", case_id=cid)
    started = call(app, "wt_run", case_id=cid, iters=200)
    assert wait_job(app, started["job"])["state"] == "done"
    bare = call(app, "wt_result", case_id=cid)
    assert bare["cl"] is None and bare["verdict"]["state"] == "converged"
    assert "residuals only" in bare["verdict"]["notes"][0] and "forces=" in bare["note"]
    started = call(app, "wt_run", case_id=cid, iters=200, forces={"patches": ["airfoil"]})
    assert wait_job(app, started["job"])["state"] == "done"
    res = call(app, "wt_result", case_id=cid)
    assert res["cl"] == pytest.approx(0.4356, abs=2e-3) and res["verdict"]["state"] == "converged"
    run = app._wt_store.load(cid)["runs"][-1]
    assert run["forces"]["lRef"] == pytest.approx(1.0, rel=1e-3)
    assert run["forces"]["lRef_source"].startswith("measured")
    assert run["forces"]["Aref"] == pytest.approx(0.1, rel=0.05)  # chord x the slab depth
    assert run["forces"]["dragDir"] == [1.0, 0.0, 0.0]
    control = (Path(run["run_dir"]) / "system" / "controlDict").read_text()
    assert "forceCoeffs" in control and "patches" in control
    edir = Path(app._wt_store.load(cid)["engine_dir"])
    assert "forceCoeffs" not in (edir / "system" / "controlDict").read_text()  # the adopted copy
    assert sorted(p.relative_to(src) for p in src.rglob("*")) == before  # the source
    with pytest.raises(TeeError) as err:  # an empty patches list falls back to the walls; a
        call(app, "wt_run", case_id=cid, iters=200, forces={"U": [0, 0, 0]})  # zero U cannot
    assert err.value.code == "wt_refs_needed"
