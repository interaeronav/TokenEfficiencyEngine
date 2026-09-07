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
