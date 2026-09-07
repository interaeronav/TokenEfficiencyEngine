"""A72 P2-P5, the `cfd` tier: the same loop on the REAL engines.

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
import subprocess
import time
from pathlib import Path

import pytest
from fixtures_windtunnel import wait_job

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.windtunnel import airfoil, engines, foam, runs
from tee.windtunnel.runner import pid_alive
from tee.windtunnel.tools import TOLERATED_CHECKS, register_windtunnel_tools

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


def call(app, tool, /, **args):
    # positional-only, because `wt_open app=openvsp` is an argument named app
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


def test_the_tmr_flat_plate_reproduces_its_reference_on_real_openfoam(app):
    """The turbulence-model verification case: a kOmegaSST zero-pressure-
    gradient plate at Re_L 5e6, checked on a LOCAL quantity - Cf at
    x = 0.9700840712 - read from a wall-shear sample rather than an
    integrated force. -1.6 % on this machine, and the sign is expected: the
    TMR states this is a compressible verification case and simpleFoam is
    incompressible.
    """
    _need("openfoam")
    out = call(app, "wt_verify", case="flatplate", confirm_cost=True)
    r = out["results"][0]
    assert abs(r["Re"] - 5.0e6) / 5.0e6 < 1e-4, "the benchmark's Reynolds number, or it is not one"
    assert r["engine"] == "openfoam" and r["verdict"] in ("converged", "stalled")
    cf = r["checks"]["cf"]
    assert cf["at_x"] == 0.9700840712
    assert abs(cf["pct"]) <= cf["tol_pct"] and r["pass"] is True
    assert 2.4e-3 < cf["measured"] < 3.0e-3
    assert r["wall_samples"] > 100  # the sampler wrote the whole wall


def test_wt_verify_all_passes_on_the_real_engines(app):
    _need("su2")
    _need("vspaero")
    _need("openfoam")
    out = call(app, "wt_verify", case="all", confirm_cost=True)
    assert out["all_pass"] is True, out
    assert set(out["skipped_unverified"]) == set()
    assert set(out["skipped_unimplemented"]) == set()  # every runner is built now


def test_the_re40_cylinder_reproduces_its_reference_on_real_openfoam(app):
    """The bluff-body benchmark end to end: a laminar O-mesh cylinder run
    at Re 40 EXACTLY, against the open reference solution of Gautier, Biau
    & Lamballais (Computers & Fluids 75, 2013). +1.7 % on this machine -
    the gap a second-order finite-volume mesh with a finite domain should
    have against a spectral solution with asymptotic far-field conditions.
    """
    _need("openfoam")
    out = call(app, "wt_verify", case="cylinder_re40", confirm_cost=True)
    r = out["results"][0]
    assert r["Re"] == 40.0, "a benchmark at the wrong Reynolds number is not a benchmark"
    assert r["engine"] == "openfoam" and r["verdict"] == "converged"
    cd = r["checks"]["cd"]
    assert abs(cd["pct"]) <= cd["tol_pct"] and r["pass"] is True
    assert 1.4 < cd["measured"] < 1.65  # the literature band the reference paper tabulates
    # ParaView is optional here: without it the wake reports itself skipped
    wake = r["checks"]["wake_lw_over_d"]
    assert wake.get("measured") is not None or wake.get("skipped")


# -- A73: the GUI handoff, on the real ParaView and OpenVSP -------------------
#
# Measured 2026-09-07 (ParaView 5.11.2 apt + xvfb, OpenVSP 3.51.3, OpenFOAM
# v2606). Running these found three defects the hermetic tests could not see,
# because a fake pvpython accepts any script: `ColorBy(d, None)` raises on a
# case with no field arrays; a state that sets only `rv.ViewTime` reloads at
# t=0; and `wt_open` on an SU2 case raised NameError, the reader block having
# bound `ts` for .foam and not for .vtu. All three are fixed and pinned here -
# a handoff that opens the initial field while the human believes it is the
# solution is worse than one that refuses.


def _loadback(app, pvsm: str, *, render: bool) -> dict:
    """Open a state in a FRESH pvpython and report what ParaView built.

    The point of the whole campaign in one function: a state file is only a
    handoff if another process, started from nothing, arrives at the case.
    """
    from tee.windtunnel import engines as eng
    from tee.windtunnel import paraview as pv

    script = """
from paraview.simple import *
import json
LoadState(__PVSM__)
src = [v for k, v in GetSources().items()][0]
views = GetViews()
rv = views[0] if views else None
if rv is not None:
    SetActiveView(rv)
src.UpdatePipeline(rv.ViewTime if rv is not None else 0.0)
facts = {
    'reader': src.__class__.__name__,
    'file': str(getattr(src, 'FileName', '')),
    'arrays': list(getattr(src, 'CellArrays', []) or []),
    'views': [v.__class__.__name__ for v in views],
    'scene_time': float(GetAnimationScene().AnimationTime),
    'timesteps': [float(t) for t in (src.TimestepValues or [])],
    'cells': int(src.GetDataInformation().GetNumberOfCells()),
}
if rv is not None:
    d = GetDisplayProperties(src, rv)
    facts['view_time'] = float(rv.ViewTime)
    facts['representation'] = str(d.Representation).strip("'")
    facts['colour'] = [str(x) for x in d.ColorArrayName]
    facts['camera'] = [float(x) for x in rv.CameraPosition]
print('FACTS ' + json.dumps(facts))
print('OK')
""".replace("__PVSM__", repr(pvsm))
    out = pv.run_script(
        eng.find_pvpython({}).path,
        script,
        Path(pvsm).parent / "_loadback",
        render=render,
        timeout_s=300,
    )
    return json.loads(next(ln for ln in out.splitlines() if ln.startswith("FACTS "))[6:])


@pytest.fixture(scope="module")
def meshed_case(app):
    """A case with a mesh and no run: the handoff before the hour is spent."""
    _need("openfoam")
    cid = call(app, "wt_case", action="create", naca="2412", V_mps=25, aoa_deg=2)["case_id"]
    assert call(app, "wt_mesh", case_id=cid, nj=40)["ok"] is True
    return cid


def test_a_state_over_a_solved_case_loads_back_at_the_converged_time(app, foam_case):
    """206,584 bytes over 16,000 cells, written in 4.5 s and read back in 3.6 s.

    The time assertion is the one that matters: before the animation scene was
    written into the state, this came back 0.0 - ParaView would have opened the
    initial field, coloured and captioned as if it were the answer.
    """
    from tee.windtunnel import state as state_mod

    _need("pvpython")
    t0 = time.time()
    out = call(app, "wt_open", case_id=foam_case)
    latest = app._wt_store.load(foam_case)["runs"][-1]
    assert out["launched"] is False and out["run_id"] == latest["run_id"]
    assert out["source"].startswith(latest["run_dir"]), "the newest run's fields, not the case's"
    assert out["kind"] == ("full" if state_mod.can_render() else "pipeline")
    assert out["state"].endswith("/views/pressure.pvsm")
    assert Path(out["state"]).parent.parent == Path(out["source"]).parent, "beside what it opens"
    assert 20_000 < out["bytes"] < 2_000_000, out["bytes"]
    assert time.time() - t0 < 60

    facts = _loadback(app, out["state"], render=out["kind"] == "full")
    assert facts["reader"] == "OpenFOAMReader" and facts["file"] == out["source"]
    assert facts["cells"] == 16000 and facts["timesteps"], facts
    assert facts["scene_time"] == facts["timesteps"][-1] > 0
    if out["kind"] == "full":
        assert facts["view_time"] == facts["timesteps"][-1]
        assert facts["colour"] == ["CELLS", "p"] and facts["representation"] == "Surface"
        assert facts["camera"][2] > 1.0, "ResetCamera ran: the case is in frame"


def test_a_state_over_a_meshed_case_with_no_run_opens_the_mesh(app, meshed_case):
    """The regression test for the ColorBy defect.

    `wt_open view=mesh` on a case that has not run is the one path where the
    data carries no array at all, and it is precisely the path a human wants
    before spending an hour. It crashed on the real ParaView until 2026-09-07;
    179,725 bytes now, run_id None, and the source is the case's own stub
    rather than a run's.
    """
    from tee.windtunnel import state as state_mod

    _need("pvpython")
    out = call(app, "wt_open", case_id=meshed_case, view="mesh")
    assert out["run_id"] is None and out["view"] == ("mesh" if out["kind"] == "full" else None)
    assert out["source"].endswith("/openfoam/case.foam"), out["source"]
    facts = _loadback(app, out["state"], render=out["kind"] == "full")
    assert facts["cells"] > 0 and facts["file"] == out["source"]
    if out["kind"] == "full":
        assert facts["representation"] == "Surface With Edges"
        assert facts["colour"][1] == "", "a mesh view is not coloured by anything"
    assert state_mod.can_render() or out["kind"] == "pipeline"


def test_a_relocated_state_opens_the_case_it_was_moved_to(app, foam_case, tmp_path):
    """`relocate` is a string substitution because the path appears once, and
    this is the test that the once is true of a state ParaView actually wrote."""
    from tee.windtunnel import state as state_mod

    _need("pvpython")
    out = call(app, "wt_open", case_id=foam_case, view="velocity")
    run_dir = Path(out["source"]).parent
    moved = tmp_path / "moved_run"
    shutil.copytree(run_dir, moved)
    pvsm = moved / "views" / Path(out["state"]).name
    assert state_mod.relocate(pvsm, run_dir, moved) == 1
    facts = _loadback(app, str(pvsm), render=out["kind"] == "full")
    assert facts["file"] == str(moved / "case.foam") and facts["cells"] == 16000
    assert state_mod.relocate(pvsm, run_dir, moved) == 0, "nothing left pointing at the old path"


def test_a_pipeline_state_is_written_and_read_with_no_display_at_all(app, foam_case):
    """17,233 bytes, rc 0, no xvfb in either direction - the kind a machine
    that cannot render still gets, carrying the same reader, arrays and time."""
    from tee.windtunnel import engines as eng
    from tee.windtunnel import state as state_mod

    _need("pvpython")
    source = Path(call(app, "wt_open", case_id=foam_case)["source"])
    out = state_mod.write(
        eng.find_pvpython({}).path,
        source,
        source.parent / "views" / "pipeline.pvsm",
        kind="pipeline",
    )
    assert out["kind"] == "pipeline" and out["view"] is None
    assert out["bytes"] < 50_000, "a pipeline state is a fraction of a full one"
    facts = _loadback(app, str(out["state"]), render=False)
    assert facts["views"] == [], "nothing is shown, which is why it needs no display"
    assert facts["reader"] == "OpenFOAMReader" and facts["cells"] == 16000
    assert facts["scene_time"] == facts["timesteps"][-1] > 0


def test_the_openvsp_route_names_a_model_openvsp_reads_back(app):
    """The other half of the handoff: no state file, the .vsp3 itself.

    Verified by asking OpenVSP - `vsp -script` on a script that reads the file
    the command line names - rather than by the file existing: 86,830 bytes,
    one geom, `WingGeom` of type `Wing`.
    """
    import subprocess

    vsp = _need("vspaero")
    created = call(
        app,
        "wt_case",
        action="create",
        wing={"span": 10, "root_chord": 1, "airfoil": "0012"},
        V_mps=34,
        aoa_deg=4,
    )
    out = call(app, "wt_open", case_id=created["case_id"], app="openvsp")
    target = Path(out["target"])
    assert out["launched"] is False and target.suffix == ".vsp3" and target.is_file()
    assert out["command"][-1] == str(target) and "state" not in out
    assert out["command"][0].endswith(("vsp", "vsp.exe")), out["command"]

    script = Path(out["target"]).with_name("readback.vspscript")
    script.write_text(
        "void main()\n{\n"
        f'    ReadVSPFile( "{target}" );\n'
        "    array< string > gids = FindGeoms();\n"
        '    Print( "GEOMS=", false );\n'
        "    Print( gids.size(), true );\n"
        "    for ( uint i = 0; i < gids.size(); i++ )\n"
        '        Print( "GEOM=" + GetGeomName( gids[i] ), true );\n'
        '    Print( "DONE" );\n}\n'
    )
    res = subprocess.run(
        [vsp["path"], "-script", str(script)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(script.parent),
    )
    text = res.stdout + res.stderr
    assert "DONE" in text and "ERR" not in text, text[-400:]
    assert "GEOMS=  1" in text.replace("\t", " ") and "WingGeom" in text, text[-400:]


def test_a_state_over_an_su2_volume_file_writes_and_loads(app, tmp_path):
    """The other engine's source, which never worked: `wt_open` on an SU2 case
    raised `NameError: ts` on the real pvpython until 2026-09-07, because the
    `.vtu` reader block bound `src` and not `ts`.

    The file here is the minimal valid `UnstructuredGrid` SU2's writer shape
    reduces to - the test is of the reader block, not of the data.
    """
    from tee.windtunnel import engines as eng
    from tee.windtunnel import state as state_mod

    _need("pvpython")
    vtu = tmp_path / "flow.vtu"
    vtu.write_text(
        '<?xml version="1.0"?>\n<VTKFile type="UnstructuredGrid" version="0.1">\n'
        '<UnstructuredGrid><Piece NumberOfPoints="0" NumberOfCells="0"/>'
        "</UnstructuredGrid></VTKFile>\n"
    )
    out = state_mod.write(eng.find_pvpython({}).path, vtu, tmp_path / "views" / "pressure.pvsm")
    assert out["kind"] == ("full" if state_mod.can_render() else "pipeline")
    assert out["bytes"] > 1000 and Path(out["state"]).is_file()
    facts = _loadback(app, str(out["state"]), render=out["kind"] == "full")
    # the .vtu reader's FileName is a LIST, unlike the .foam reader's string
    assert facts["reader"] == "XMLUnstructuredGridReader" and "flow.vtu" in facts["file"]


# -- A74: cfMesh against snappyHexMesh, on the real binaries ------------------
#
# The campaign's acceptance (A74 law 3): a mesh that covers its boundary layer
# and does not move the forces has not earned a `mesher=` argument. Measured
# 2026-09-07 on the prism at alpha 0, 200 iterations, same domain and layers:
#
#   snappy                 46,160 cells  11.1 s  STALLED (2.03)  Cl 0.07458  Cd 0.4343
#   cfmesh, plain STL      38,352 cells   3.7 s  converged       Cl 0.01194  Cd 0.3146
#   cfmesh, feature edges  36,768 cells   4.1 s  converged       Cl 0.00004  Cd 0.3076
#
# The Cl column is the one that decides it. The section is symmetric and the
# incidence is zero, so lift MUST be zero: 0.0746 is the mesh talking. That is
# the invariant asserted here - a physical truth rather than a golden number.
#
# The third row is what ships, and it was a P3 surprise: the feature edges were
# added to clear twelve skew faces (they did), and they took the spurious lift
# down with them by another factor of ~300. A trailing edge the mesher rounds
# off asymmetrically is lift that is not there.


@pytest.fixture(scope="module")
def prism_stl(tmp_path_factory):
    stl = tmp_path_factory.mktemp("a74") / "prism.stl"
    airfoil.extrude_stl(stl, airfoil.naca4("0012", 24), span=0.4, chord=0.3, name="section")
    return stl


def _mesh_and_solve(app, stl, mesher: str) -> dict:
    cid = call(app, "wt_case", action="create", stl=str(stl), V_mps=20, aoa_deg=0)["case_id"]
    args = {"case_id": cid, "base_cell_m": 0.15, "levels": [1, 2], "layers": 2}
    if mesher != "snappy":
        args["mesher"] = mesher
    t0 = time.time()
    status = wait_job(app, call(app, "wt_mesh", **args)["job"], timeout_s=2400)
    assert status["state"] == "done", status
    mesh = status["result"]
    mesh["mesh_wall_s"] = round(time.time() - t0, 1)
    started = call(app, "wt_run", case_id=cid, iters=200, confirm_cost=True)
    assert wait_job(app, started["job"], timeout_s=3600)["state"] == "done"
    return {"case_id": cid, "mesh": mesh, "result": call(app, "wt_result", case_id=cid)}


def test_cfmesh_meshes_the_prism_and_solves_on_it(app, prism_stl):
    """The integration P2 existed to prove, and the defect it found first.

    A patch in a cfMesh case is an STL `solid`, so the first attempt - one
    `farfield` solid - meshed perfectly and stopped `simpleFoam` dead at
    "Cannot find patchField entry for farfield". The box carries blockMesh's
    own patch names now, and this test fails the moment that regresses.
    """
    _need("openfoam")
    out = _mesh_and_solve(app, prism_stl, "cfmesh")
    mesh, res = out["mesh"], out["result"]
    assert mesh["kind"] == "cfmesh" and mesh["cells"] > 10_000
    assert mesh["threads"] == 1 and mesh["reproducible"] is True
    assert res["cd"] is not None and res["cl"] is not None
    edir = Path(app._wt_store.load(out["case_id"])["engine_dir"])
    boundary = (edir / "constant" / "polyMesh" / "boundary").read_text()
    for patch in ("inlet", "outlet", "sides", "top", "ground", "body"):
        assert patch in boundary, f"{patch} missing: the 0/ fields name it"
    app._a74_cfmesh = out


def test_the_symmetric_section_at_zero_incidence_has_no_lift_on_cfmesh(app, prism_stl):
    """The acceptance, and the honest version of it.

    A NACA 0012 at alpha 0 must produce ZERO lift, so any Cl at all is the
    mesh's asymmetry rather than the flow's. Measured 2026-09-07 on the same
    case: snappy 0.07458, cfMesh from a plain STL 0.01194, and cfMesh from the
    feature-edge FMS this lane now writes **0.00004** - which is zero to every
    decimal a 200-iteration RANS run can defend. The ratio against snappy is
    the claim; the absolute band below is a guard against nonsense, set two
    orders above what was measured so it cannot start reporting the weather.

    The scatter deserves its own sentence. Before OMP_NUM_THREADS=1 became the
    default, three runs of this case gave 0.0013, 0.0093 and 0.0119, because a
    threaded cfMesh built a different mesh each time. The band was first set at
    0.01 from the first of those - which is how a threshold ends up measuring
    whichever run happened to be luckiest.
    """
    _need("openfoam")
    cf = getattr(app, "_a74_cfmesh", None) or _mesh_and_solve(app, prism_stl, "cfmesh")
    assert abs(cf["result"]["cl"]) < 0.005, "spurious lift beyond anything measured here"
    assert cf["result"]["verdict"]["state"] == "converged"
    assert cf["result"]["uncertainty"]["trust"] == "comparative"

    sn = _mesh_and_solve(app, prism_stl, "snappy")
    # Recorded rather than asserted: snappy's spurious lift is a fact about
    # this geometry at this refinement, not a promise the lane makes.
    print(
        f"\nA74 P2: cl cfmesh {cf['result']['cl']:+.5f} vs snappy {sn['result']['cl']:+.5f}; "
        f"cd {cf['result']['cd']:.5f} vs {sn['result']['cd']:.5f}; "
        f"verdict {cf['result']['verdict']['state']} vs {sn['result']['verdict']['state']}; "
        f"cells {cf['mesh']['cells']} vs {sn['mesh']['cells']}; "
        f"mesh {cf['mesh']['mesh_wall_s']} s vs {sn['mesh']['mesh_wall_s']} s"
    )
    assert abs(cf["result"]["cl"]) < 0.5 * abs(sn["result"]["cl"]), (
        "the cartesian mesh is the symmetric one"
    )


def test_cfmesh_meshes_the_same_case_to_the_same_mesh_by_default(app, prism_stl):
    """The reproducibility the default buys, on the real binary.

    Threaded, cfMesh answered 7c260615fd23772e and cc2a2a95b348336a to the same
    question (2026-09-07). snappy answered b0b9f5b5b90059d8 twice. A mesh hash
    that changes for the same input cannot do the job this lane gives it - it
    travels with every coefficient, and same-mesh deltas are the first-class
    claim - so `wt_mesh mesher=cfmesh` pins OMP_NUM_THREADS=1 and pays about
    25 % of a few seconds for an answer that repeats.
    """
    _need("openfoam")
    hashes = []
    for _ in range(2):
        cid = call(app, "wt_case", action="create", stl=str(prism_stl), V_mps=20)["case_id"]
        status = wait_job(
            app,
            call(app, "wt_mesh", case_id=cid, mesher="cfmesh", base_cell_m=0.15, layers=2)["job"],
            timeout_s=1200,
        )
        assert status["state"] == "done", status
        assert status["result"]["reproducible"] is True
        hashes.append(status["result"]["mesh_hash"])
    assert hashes[0] == hashes[1], f"cfMesh answered differently twice: {hashes}"


def _mesh_without_features(app, stl) -> dict:
    """A74 P3's other arm: the same case meshed from the plain STL.

    `feature_angle` is deliberately not a caller argument (A74 law 5), so this
    reaches past the tool to the writer - which is the only honest way to
    measure what the feature step BUYS. It runs the real binaries by the same
    argv the lane would, single-threaded, and returns `checkMesh`'s digest.
    """
    cid = call(app, "wt_case", action="create", stl=str(stl), V_mps=20, aoa_deg=0)["case_id"]
    rec = app._wt_store.load(cid)
    edir = Path(rec["engine_dir"])
    runs.write_tunnel_3d_cfmesh(
        rec, edir, base_cell_m=0.15, body_cell_m=0.0375, layers=2, feature_angle=0
    )
    install = engines.find_openfoam({}, probe_version=False)
    for name, argv in runs.mesh_sequence_3d_cfmesh(install, edir, 1, feature_angle=0):
        res = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=1800,
            cwd=str(edir),
            env={**os.environ, "OMP_NUM_THREADS": "1"},
        )
        (edir / f"log.{name}").write_text(res.stdout + res.stderr)
        assert res.returncode == 0, f"{name} rc={res.returncode}: {res.stderr[-300:]}"
    return foam.parse_checkmesh((edir / "log.checkMesh").read_text())


def test_feature_edges_earn_the_clean_checkmesh_the_plain_surface_cannot(app, prism_stl):
    """A74 P3's acceptance: `checkMesh` passes CLEAN, without widening anything.

    cfMesh rounds a sharp trailing edge off into skew cells unless it is told
    where the edges are. Measured 2026-09-07 on this prism: from the plain STL,
    max skewness 5.5497203 with twelve faces flagged and `checkMesh` FAILING;
    from the FMS `surfaceFeatureEdges -angle 30` writes, 2.0995350 and a clean
    pass, for 0.4 s and 1,584 fewer cells. 45 degrees also passes and is worse
    (2.2391098). `edgeMeshRefinement` - cfMesh's own key for refining along
    those edges - was tried and killed `cartesianMesh` with rc=1, so it is not
    shipped (doc 74 section 2.8).

    Both halves are asserted because skew is one of `TOLERATED_CHECKS`: a mesh
    that FAILS this check would still run under that tolerance, which is
    exactly what A74 law 4 forbids buying the pass with.
    """
    _need("openfoam")
    cf = getattr(app, "_a74_cfmesh", None) or _mesh_and_solve(app, prism_stl, "cfmesh")
    good = cf["mesh"]
    assert good["feature_angle"] == 30.0
    assert good.get("failed") in ([], None), f"the feature route did not pass clean: {good}"
    assert good.get("failed_checks", 0) == 0, good
    assert good["ok"] is True

    plain = _mesh_without_features(app, prism_stl)
    print(
        f"\nA74 P3: skew {good['max_skew']} clean vs {plain['max_skew']} with "
        f"{len(plain.get('failed') or [])} failed; cells {good['cells']} vs {plain['cells']}"
    )
    assert plain.get("failed"), (
        "the plain surface passed checkMesh: cfMesh's own behaviour has changed "
        "and the feature step is no longer what earns the clean pass"
    )
    assert float(good["max_skew"]) < float(plain["max_skew"])
    assert TOLERATED_CHECKS == ("skew", "upper triangular"), (
        "A74 law 4: the pass is earned by fixing the mesh, never by widening this"
    )
