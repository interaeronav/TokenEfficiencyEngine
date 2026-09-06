"""A68 P2-P5, the `cfd` tier: the same loop on the REAL engines.

Deselected by default (`addopts = -m "not cfd"`); `uv run pytest -m cfd
tests/test_windtunnel_live.py` runs whatever this machine has and skips the
rest BY NAME with the install line. Measured 2026-09-06 in the Linux
container (OpenFOAM v2606 from dl.openfoam.com, SU2 8.4.0 linux64, OpenVSP
3.51.3 deb, ParaView 5.11.2 apt + xvfb): the whole file takes about four
minutes. Nothing here vendors a tutorial: the apt airFoil2D adoption smoke
runs it in place when TEE_WT_TUTORIAL (or the apt path) exists.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

import pytest
from fixtures_windtunnel import wait_job

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.windtunnel import airfoil, engines
from tee.windtunnel.runner import pid_alive
from tee.windtunnel.tools import register_windtunnel_tools

# the repo's 60 s per-test timeout is for hermetic tests; a real SU2 Euler run
# is ~90 s and `wt_verify all` about two minutes (measured 2026-09-06)
pytestmark = [pytest.mark.cfd, pytest.mark.timeout(900)]

TUTORIAL = Path(
    os.environ.get(
        "TEE_WT_TUTORIAL",
        "/usr/share/doc/openfoam-examples/examples/incompressible/simpleFoam/airFoil2D",
    )
)


def _have(engine: str) -> dict:
    return engines.probe({})["engines"][engine]


def _need(engine: str):
    found = _have(engine)
    if not found.get("found"):
        pytest.skip(f"{engine} absent: {found.get('fix')}")
    return found


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    project = tmp_path_factory.mktemp("wt_live")
    application = TeeApp({"fake": FakeAdapter()}, project_root=project)
    store = register_windtunnel_tools(application, project)
    application._wt_store = store
    try:
        yield application
    finally:
        application.shutdown()


def call(app, tool, **args):
    return app.registry.call(tool, args)


@pytest.fixture(scope="module")
def foam_case(app):
    """NACA 0012, 30 m/s, 4 deg, TEE's 16,000-cell O-mesh, simpleFoam kOmegaSST."""
    _need("openfoam")
    created = call(app, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=4)
    cid = created["case_id"]
    mesh = call(app, "wt_mesh", case_id=cid, nj=80)
    assert mesh["ok"] is True and mesh["cells"] == 16000, mesh
    t0 = time.time()
    started = call(app, "wt_run", case_id=cid, iters=600)
    status = wait_job(app, started["job"], timeout_s=600)
    assert status["state"] == "done", status
    app._wt_live_wall = time.time() - t0
    return cid


# -- OpenFOAM ---------------------------------------------------------------


def test_openfoam_two_d_case_converges_to_the_measured_figure(app, foam_case):
    """Measured 2026-09-06: 197 iterations, 17 s, Cl 0.4356 (thin airfoil
    2 pi alpha = 0.4386, -0.7 %), Cd 0.0109 (Abbott & von Doenhoff 0.0095-0.0100
    at Re 2-3e6: +10 %, a coarse mesh) - comparative, not absolute."""
    res = call(app, "wt_result", case_id=foam_case)
    assert res["verdict"]["state"] == "converged", res["verdict"]
    assert res["cl"] == pytest.approx(0.4356, abs=0.01)
    assert 0.0095 <= res["cd"] <= 0.013
    assert res["uncertainty"]["trust"] == "comparative" and res["engine_version"].startswith("v")
    assert app._wt_live_wall < 120
    status = call(app, "wt_status", case_id=foam_case)
    assert status["state"] == "done" and status["verdict"] == "converged"


def test_openfoam_cancel_kills_a_real_solver_within_two_seconds(app, foam_case):
    started = call(app, "wt_run", case_id=foam_case, iters=100_000, confirm_cost=True)
    time.sleep(3.0)
    mid = call(app, "wt_status", case_id=foam_case)
    assert mid["state"] == "running" and mid.get("iter", 0) > 0, mid
    run = app._wt_store.load(foam_case)["runs"][-1]
    pid = json.loads((Path(run["run_dir"]) / "run.json").read_text())["pid"]
    assert pid_alive(pid)
    t0 = time.time()
    app.jobs.cancel(started["job"])
    deadline = time.time() + 5
    while time.time() < deadline and pid_alive(pid):
        time.sleep(0.02)
    assert not pid_alive(pid) and time.time() - t0 < 2.0
    wait_job(app, started["job"])
    assert app._wt_store.load(foam_case)["runs"][-1]["state"] == "cancelled"
    partial = call(app, "wt_result", case_id=foam_case, allow_partial=True)
    assert partial["verdict"]["state"] == "cancelled" and partial["iters_used"] > 0


def test_openfoam_parallel_run_agrees_with_serial(app, foam_case):
    if not shutil.which("mpirun") and not _have("openfoam").get("mpirun"):
        pytest.skip("no mpirun on this machine")
    serial = call(app, "wt_result", case_id=foam_case, run_id="run_001")
    started = call(app, "wt_run", case_id=foam_case, iters=600, cores=2, confirm_cost=True)
    status = wait_job(app, started["job"], timeout_s=600)
    assert status["state"] == "done", status
    par = status["result"]
    assert par["cl"] == pytest.approx(serial["cl"], abs=1e-3)
    assert par["cd"] == pytest.approx(serial["cd"], abs=1e-4)
    run = app._wt_store.load(foam_case)["runs"][-1]
    assert "-parallel" in " ".join(run["argv"])
    if os.geteuid() == 0:
        assert run["mpi_root_override"] is True


def test_openfoam_fields_are_sampled_render_free_and_rendered_offscreen(app, foam_case):
    pv = _have("pvpython")
    if not pv.get("found"):
        pytest.skip(f"pvpython absent: {pv.get('fix')}")
    line = call(
        app,
        "wt_probe_field",
        case_id=foam_case,
        run_id="run_001",
        field="U",
        p1=[0.5, 0.0, 0.05],
        p2=[0.5, 0.3, 0.05],
        n=16,
    )
    assert line["n"] == 16 and line["outside_mesh"] >= 1  # the first samples sit in the body
    valid = [v for v in line["U_mag"] if v is not None]
    assert valid and 25.0 < max(valid) < 40.0, line["U_mag"]
    try:
        view = call(app, "wt_view", case_id=foam_case, run_id="run_001", view="pressure")
    except TeeError as exc:
        assert exc.code == "wt_render_failed" and "xvfb" in exc.fix
        pytest.skip("no offscreen rendering here (the refusal names the fix)")
    assert Path(view["png"]).stat().st_size > 1000 and view["colour_range"]["min"] < 0


def test_openfoam_three_d_prism_meshes_with_snappy_and_runs(app, tmp_path):
    _need("openfoam")
    stl = tmp_path / "prism.stl"
    airfoil.extrude_stl(stl, airfoil.naca4("0012", 24), span=0.4, chord=0.3)
    created = call(app, "wt_case", action="create", stl=str(stl), V_mps=20, aoa_deg=0)
    cid = created["case_id"]
    started = call(app, "wt_mesh", case_id=cid, base_cell_m=0.15, levels=[1, 2], layers=2)
    status = wait_job(app, started["job"], timeout_s=900)
    assert status["state"] == "done", status
    mesh = status["result"]
    assert mesh["cells"] > 5000 and mesh["kind"] == "snappy"
    run = call(app, "wt_run", case_id=cid, iters=150, confirm_cost=True)
    status = wait_job(app, run["job"], timeout_s=900)
    assert status["state"] == "done", status
    res = status["result"]
    assert res["cd"] is not None and res["verdict"]["state"] in (
        "converged",
        "stalled",
        "insufficient",
        "oscillating",
    )


def test_adopting_the_apt_tutorial_runs_it_with_measured_forces(app):
    _need("openfoam")
    if not (TUTORIAL / "system" / "controlDict").is_file():
        pytest.skip(f"no airFoil2D tutorial at {TUTORIAL} (set TEE_WT_TUTORIAL)")
    adopted = call(app, "wt_case", action="adopt", path=str(TUTORIAL))
    cid = adopted["case_id"]
    assert adopted["solver"] == "simpleFoam" and adopted["has_forceCoeffs"] is False
    mesh = call(app, "wt_mesh", case_id=cid)
    assert mesh["has_mesh"] is True and mesh["ok"] is True  # 'upper triangular order' tolerated
    started = call(app, "wt_run", case_id=cid, confirm_cost=True, forces={"patches": ["walls"]})
    status = wait_job(app, started["job"], timeout_s=900)
    assert status["state"] == "done", status
    res = call(app, "wt_result", case_id=cid)
    run = app._wt_store.load(cid)["runs"][-1]
    assert run["forces"]["lRef"] == pytest.approx(35.05, rel=0.01)  # measured from the mesh
    assert res["verdict"]["state"] == "converged"
    assert 0.8 < res["cl"] < 1.1 and 0.02 < res["cd"] < 0.04  # alpha 8 deg, SA, 35 m section


# -- SU2 -----------------------------------------------------------------------


def test_su2_euler_naca0012_reproduces_the_quickstart_figure(app):
    _need("su2")
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
    mesh = call(app, "wt_mesh", case_id=cid, first_cell_c=0.005, nj=50)
    assert mesh["ok"] is True
    started = call(app, "wt_run", case_id=cid, iters=3000, confirm_cost=True)
    status = wait_job(app, started["job"], timeout_s=900)
    assert status["state"] == "done", status
    res = status["result"]
    assert res["verdict"]["state"] == "converged"
    assert res["cl"] == pytest.approx(0.328486, rel=0.05)  # the official mesh: +1.8 % measured
    assert res["cd"] == pytest.approx(0.021481, rel=0.15)  # -7.3 % measured (wave drag, coarse)


# -- OpenVSP / VSPAERO --------------------------------------------------------------


def test_vspaero_wing_sweep_sits_inside_the_lifting_line_band(app):
    _need("vspaero")
    created = call(
        app,
        "wt_case",
        action="create",
        wing={"span": 10, "root_chord": 1, "airfoil": "0012"},
        V_mps=34,
        aoa_deg=4,
    )
    cid = created["case_id"]
    started = call(app, "wt_sweep", case_id=cid, aoa=[0, 2, 4, 6], cores=4)
    status = wait_job(app, started["job"], timeout_s=300)
    assert status["state"] == "done", status
    res = status["result"]
    assert res["cl_alpha_per_rad"] == pytest.approx(5.19, rel=0.08)  # measured 4.905 (-5.5 %)
    assert len(res["polar"]) == 4 and abs(res["polar"][0]["cl"]) < 0.005


def test_wt_verify_all_passes_on_the_real_engines(app):
    _need("su2")
    _need("vspaero")
    out = call(app, "wt_verify", case="all", confirm_cost=True)
    assert out["all_pass"] is True, out
    assert set(out["skipped_unverified"]) == {"cylinder_re40", "flatplate"}
