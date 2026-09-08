"""A73 — the GUI handoff, driven with no ParaView and no window anywhere.

Every test here runs against the fake engines: `fake-pv/pvpython` answers a
`SaveState(...)` script by writing a state whose size and single source path
are what the lane reads back, `fake-pv/paraview` and `fake-vsp/vsp` stand in
for the two applications and write a marker instead of holding a window. So
the whole tool - prepare, refuse, launch - is exercised on a machine with no
display, which is where this code has to be right.

The one thing fakes cannot prove is that ParaView itself accepts what was
written; `test_windtunnel_live.py` does that under the `cfd` marker.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures_windtunnel import install_fakes, make_app, wait_job

from tee.kernel.errors import TeeError


def call(app, name, /, **args):
    return app.registry.call(name, args)


@pytest.fixture
def solved(tmp_path):
    """A case that has been meshed and run, and its app."""
    app = make_app(tmp_path)
    cid = call(app, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=4)["case_id"]
    call(app, "wt_mesh", case_id=cid, nj=20, n_surface=30)
    job = call(app, "wt_run", case_id=cid, confirm_cost=True)["job"]
    wait_job(app, job, 60)
    return app, cid


# -- prepare -----------------------------------------------------------------


def test_prepare_writes_a_state_and_returns_the_command_without_opening_anything(solved):
    app, cid = solved
    r = call(app, "wt_open", case_id=cid)
    assert r["app"] == "paraview"
    assert r["launched"] is False
    state = Path(r["state"])
    assert state.is_file() and state.suffix == ".pvsm"
    assert r["bytes"] == state.stat().st_size > 0
    # the command is both executable and pasteable
    assert r["command"][1].startswith("--state=")
    assert r["command_line"].endswith(r["state"])
    assert "launch=true" in r["note"]
    # nothing was opened
    assert not Path(str(state) + ".opened").exists()


def test_the_state_lands_beside_its_case_so_the_two_travel_together(solved):
    app, cid = solved
    r = call(app, "wt_open", case_id=cid, view="velocity")
    state, source = Path(r["state"]), Path(r["source"])
    assert state.name == "velocity.pvsm"
    assert state.parent.name == "views"
    assert state.parent.parent == source.parent  # the case dir the .foam stub sits in


def test_a_case_with_only_a_mesh_can_still_be_opened(tmp_path):
    """The A72 defect this campaign fixes: looking at a mesh BEFORE spending an
    hour solving on it is one of the better reasons to open ParaView."""
    app = make_app(tmp_path)
    cid = call(app, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=4)["case_id"]
    call(app, "wt_mesh", case_id=cid, nj=20, n_surface=30)
    r = call(app, "wt_open", case_id=cid)
    assert r["run_id"] is None
    assert Path(r["state"]).is_file()


def test_the_foam_stub_no_longer_needs_a_run(tmp_path):
    app = make_app(tmp_path)
    cid = call(app, "wt_case", action="create", naca="0012", V_mps=30, aoa_deg=4)["case_id"]
    call(app, "wt_mesh", case_id=cid, nj=20, n_surface=30)
    out = call(app, "wt_export", case_id=cid, format="foam")
    assert Path(out["path"]).name == "case.foam" and Path(out["path"]).is_file()


def test_a_pipeline_state_is_far_smaller_than_one_carrying_a_view(solved):
    app, cid = solved
    full = call(app, "wt_open", case_id=cid, kind="full")
    pipeline = call(app, "wt_open", case_id=cid, kind="pipeline")
    assert full["kind"] == "full" and full["view"] == "pressure"
    assert pipeline["kind"] == "pipeline" and pipeline["view"] is None
    assert pipeline["bytes"] * 4 < full["bytes"]


def test_asking_for_a_view_where_nothing_can_render_is_refused_not_downgraded(solved, monkeypatch):
    """A caller who asked for the coloured state should hear that they cannot
    have it, rather than be handed something else that looks like success."""
    app, cid = solved
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr("tee.windtunnel.state.shutil.which", lambda name: None)
    monkeypatch.setattr("tee.windtunnel.state.platform.system", lambda: "Linux")
    with pytest.raises(TeeError) as e:
        call(app, "wt_open", case_id=cid, kind="full")
    assert e.value.code == "wt_no_display"
    assert "pipeline" in e.value.fix
    # ... and the same machine still gets the pipeline state
    assert call(app, "wt_open", case_id=cid)["kind"] == "pipeline"


# -- the applications --------------------------------------------------------


def test_openvsp_gets_the_vsp3_and_a_case_without_one_is_refused(tmp_path):
    app = make_app(tmp_path)
    wing = call(app, "wt_case", action="create", wing={"span": 10, "root_chord": 1}, V_mps=34)
    r = call(app, "wt_open", case_id=wing["case_id"], app="openvsp")
    assert r["target"].endswith(".vsp3")
    assert r["command"][1] == r["target"]
    foil = call(app, "wt_case", action="create", naca="0012", V_mps=30)["case_id"]
    with pytest.raises(TeeError) as e:
        call(app, "wt_open", case_id=foil, app="openvsp")
    assert e.value.code == "wt_no_geometry"


def test_an_application_the_lane_does_not_hand_to_is_refused_by_name(solved):
    app, cid = solved
    with pytest.raises(TeeError) as e:
        call(app, "wt_open", case_id=cid, app="blender")
    assert e.value.code == "wt_bad_action"
    assert "paraview" in e.value.fix and "openvsp" in e.value.fix


def test_paraview_absent_still_hands_back_the_state_it_wrote(solved, monkeypatch):
    app, cid = solved
    monkeypatch.setattr(
        "tee.windtunnel.engines.find_paraview_app",
        lambda cfg: (_ for _ in ()).throw(
            TeeError("wt_paraview_missing", "not installed.", fix="Install it.")
        ),
    )
    with pytest.raises(TeeError) as e:
        call(app, "wt_open", case_id=cid)
    assert e.value.code == "wt_paraview_missing"
    assert ".pvsm" in e.value.message  # the useful half survives the refusal
    assert "--state=" in e.value.fix


# -- launch ------------------------------------------------------------------


def test_launch_opens_the_application_with_the_state_and_says_so(solved, monkeypatch):
    app, cid = solved
    monkeypatch.setenv("DISPLAY", ":0")
    r = call(app, "wt_open", case_id=cid, launch=True)
    assert r["launched"] is True and r["pid"] > 0
    marker = Path(r["state"] + ".opened")
    for _ in range(200):  # the fake exits at once; give it a moment
        if marker.exists():
            break
        import time

        time.sleep(0.02)
    assert marker.is_file()
    assert f"--state={r['state']}" in marker.read_text()


def test_launch_with_no_display_refuses_before_it_spawns(solved, monkeypatch):
    """ParaView builds its Qt application BEFORE parsing arguments, so a spawn
    here would report a Qt plugin error instead of the real one."""
    app, cid = solved
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr("tee.windtunnel.tools.platform.system", lambda: "Linux")
    with pytest.raises(TeeError) as e:
        call(app, "wt_open", case_id=cid, launch=True)
    assert e.value.code == "wt_no_display"
    assert "--state=" in e.value.fix  # the command to run where they are sitting
    assert not Path(call(app, "wt_open", case_id=cid)["state"] + ".opened").exists()


def test_openvsp_launch_opens_the_model_positionally(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    monkeypatch.setenv("DISPLAY", ":0")
    cid = call(app, "wt_case", action="create", wing={"span": 10, "root_chord": 1}, V_mps=34)[
        "case_id"
    ]
    r = call(app, "wt_open", case_id=cid, app="openvsp", launch=True)
    marker = Path(r["target"] + ".opened")
    for _ in range(200):
        if marker.exists():
            break
        import time

        time.sleep(0.02)
    assert marker.is_file()
    assert marker.read_text().strip().endswith(".vsp3")


# -- the state module's own laws ---------------------------------------------


def test_a_state_names_its_case_once_so_relocating_is_a_string_swap(solved, tmp_path):
    from tee.windtunnel import state as state_mod

    app, cid = solved
    r = call(app, "wt_open", case_id=cid)
    pvsm = Path(r["state"])
    source = Path(r["source"])
    assert pvsm.read_text().count(str(source)) == 1
    moved = tmp_path / "elsewhere" / "case.foam"
    assert state_mod.relocate(pvsm, source, moved) == 1
    assert str(moved) in pvsm.read_text()
    assert state_mod.relocate(pvsm, source, moved) == 0  # nothing left to do


def test_an_unknown_state_kind_is_refused(tmp_path):
    from tee.windtunnel import state as state_mod

    with pytest.raises(TeeError) as e:
        state_mod.state_script(Path("/x/case.foam"), Path("/x/s.pvsm"), kind="sketch")
    assert e.value.code == "wt_bad_action"


def test_the_state_script_opens_what_wt_view_renders(tmp_path):
    """One vocabulary: the handoff and the render read the same presets and the
    same reader block, so a state never shows something wt_view would not."""
    from tee.windtunnel import paraview as pv
    from tee.windtunnel import state as state_mod

    text = state_mod.state_script(Path("/x/case.foam"), Path("/x/s.pvsm"), view="velocity")
    assert "OpenFOAMReader(FileName='/x/case.foam')" in text
    assert "ColorBy(d, ('CELLS', 'U'))" in text
    assert text.startswith(f"# {pv.GENERATED_BY}")
    assert "SaveState('/x/s.pvsm')" in text and text.rstrip().endswith("print('OK')")
    with pytest.raises(TeeError) as e:
        state_mod.state_script(Path("/x/case.foam"), Path("/x/s.pvsm"), view="nonsense")
    assert e.value.code == "wt_bad_view"


def test_the_state_script_carries_the_time_and_never_colours_by_none():
    """The two defects P2 found on the real ParaView (doc 73 §2.10), pinned
    where CI can see them.

    A fake `pvpython` accepts whatever script it is handed, so the only guard
    that runs on a machine without ParaView is the text of the script itself:
    the animation scene must carry the time - `SaveState` does not save the
    view's - and `ColorBy(d, None)` must never appear, because it raises on a
    case whose data has no array to colour by.
    """
    from tee.windtunnel import state as state_mod

    for kind in state_mod.KINDS:
        text = state_mod.state_script(
            Path("/x/case.foam"), Path("/x/s.pvsm"), view="mesh", kind=kind
        )
        assert "GetAnimationScene()" in text, kind
        assert "scene.UpdateAnimationUsingDataTimeSteps()" in text, kind
        assert "scene.AnimationTime = ts[-1]" in text, kind
        assert "ColorBy(d, None)" not in text, kind

    full = state_mod.state_script(Path("/x/case.foam"), Path("/x/s.pvsm"), view="mesh", kind="full")
    assert "ColorBy(d, ('CELLS', None))" in full  # a valid association, no array
    assert "rv.ViewTime = ts[-1]" in full  # the view too, for the writing process


def test_the_reader_block_binds_ts_before_the_state_script_uses_it():
    """`wt_open` on an SU2 case died with `NameError: ts`.

    `paraview._reader_lines` bound `ts` in its `.foam` branch and not in its
    `.vtu` one, while `state_script` reads it in both - so the handoff worked
    for one engine and crashed for the other, and only on a real `pvpython`.
    The structural assertion is the one worth keeping: whatever the reader
    block grows into, it assigns `ts` before anything reads it.
    """
    from tee.windtunnel import state as state_mod

    for source in (Path("/x/case.foam"), Path("/x/flow.vtu")):
        for kind in state_mod.KINDS:
            body = state_mod.state_script(source, Path("/x/s.pvsm"), kind=kind).splitlines()
            assigned = next(i for i, ln in enumerate(body) if ln.startswith("ts = "))
            used = [i for i, ln in enumerate(body) if "ts[-1]" in ln or "len(ts)" in ln]
            assert used, (source.suffix, kind)
            assert assigned < min(used), (source.suffix, kind)


def test_the_engine_resolvers_find_the_applications_beside_their_own_binaries(tmp_path):
    from tee.windtunnel import engines

    cfg = install_fakes(tmp_path)
    assert Path(engines.find_paraview_app(cfg).path).name == "paraview"
    assert engines.find_paraview_app(cfg).via == "beside pvpython"
    assert Path(engines.find_openvsp_gui(cfg).path).name == "vsp"
    with pytest.raises(TeeError) as e:
        engines.find_paraview_app({"paraview": str(tmp_path / "nowhere")})
    assert e.value.code == "wt_bad_config"
