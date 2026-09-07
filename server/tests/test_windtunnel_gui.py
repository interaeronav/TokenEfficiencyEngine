"""A73 P3 — the panel, exercised with no Qt and no window.

PySide6 is not installed on the machine this was written on, which is exactly
why the split matters: `actions` and `shell` hold all of the logic and are
driven here directly, so nothing ships unexercised. `app` is the only module
that touches Qt, and the one thing tested about it is that importing it costs
nothing and that it refuses by naming the extra.

partkiln's lesson, quoted in its own source: a shell whose logic lived in the
widgets is how seamkiln's follow-up buttons went eleven campaigns untested.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from fixtures_windtunnel import make_app, wait_job

from tee.windtunnel.gui import actions
from tee.windtunnel.gui.shell import WindTunnelShell


@pytest.fixture
def shell(tmp_path):
    return WindTunnelShell(make_app(tmp_path))


@pytest.fixture
def with_case(shell):
    out = shell.app.registry.call(
        "wt_case", {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": 4}
    )
    shell.case_id = out["case_id"]
    return shell


# -- the controls build calls, and nothing else ------------------------------


def test_every_control_names_a_tool_the_lane_actually_registers(shell):
    """Except the one that names none: `tee_job` is an always-loaded MCP tool
    rather than a virtual one, so cancel reaches the job manager directly and
    says so, instead of naming a tool this registry does not have."""
    registered = set(shell.app.registry.names())
    for control in actions.CONTROLS:
        if control.tool is None:
            assert control.key == "cancel"
            continue
        assert control.tool in registered, f"{control.key} -> {control.tool}"


def test_a_control_builds_the_arguments_a_model_would_send():
    assert actions.open_in("wt_1", "paraview", view="velocity") == {
        "case_id": "wt_1",
        "app": "paraview",
        "view": "velocity",
    }
    assert actions.run("wt_1", cores=4)["confirm_cost"] is True
    assert actions.cancel("job_7") == {"job": "job_7"}


def test_a_control_that_cannot_build_says_what_to_do_and_calls_nothing():
    with pytest.raises(ValueError, match="Select a case"):
        actions.show_case("")
    with pytest.raises(ValueError, match="job id"):
        actions.cancel("")
    with pytest.raises(ValueError, match="paraview"):
        actions.open_in("wt_1", "blender")
    with pytest.raises(ValueError, match="not a control"):
        actions.control("nonsense")


def test_case_rows_read_only_what_the_tool_puts_on_the_wire():
    rows = actions.case_rows([{"case_id": "wt_1", "kind": "airfoil2d", "runs": [{}, {}]}])
    assert rows == [{"case_id": "wt_1", "kind": "airfoil2d", "engine": "", "runs": 2, "state": ""}]


# -- the shell ---------------------------------------------------------------


def test_the_shell_lists_creates_and_selects_through_the_registry(with_case):
    shell = with_case
    rows = shell.cases()
    assert [r["case_id"] for r in rows] == [shell.case_id]
    assert shell.select(shell.case_id)["case_id"] == shell.case_id


def test_a_refusal_comes_back_as_a_dict_the_window_can_render(shell):
    """Both kinds of failure - a control that cannot build, and a lane that
    refuses - arrive in the same shape, because a window that renders one and
    crashes on the other is a window you cannot trust."""
    bad_input = shell.call("show", case_id="")
    assert bad_input["error"] == "gui_bad_input" and "Select a case" in bad_input["fix"]

    shell.case_id = "wt_nosuchcase"
    refused = shell.call("status", case_id="wt_nosuchcase")
    assert refused["error"].startswith("wt_") and refused["fix"]
    assert any("wt_" in line for line in shell.log)


def test_running_through_the_shell_records_the_job_and_can_cancel_it(with_case):
    shell = with_case
    shell.build_mesh(nj=20, n_surface=30)
    out = shell.start_run()
    assert shell.job and out.get("job") == shell.job
    tick = shell.poll()
    assert "job" in tick and "status" in tick
    # The assertion this test was missing. `"job" in tick` was true even when
    # the tick carried {"error": "unknown_tool"} - which it did on every tick,
    # because the clock called `tee_job` through the registry that does not
    # have it. A pane that reports a job must report the job.
    assert "error" not in tick["job"], tick["job"]
    assert tick["job"]["job"] == shell.job
    assert tick["job"]["state"] in ("queued", "running", "done", "error", "cancelled")
    wait_job(shell.app, shell.job, 60)
    done = shell.cancel()  # a finished job cancels to False rather than raising
    assert "error" not in done or done["error"] == "job_cancel_failed"


def test_the_handoff_goes_through_the_same_tool_a_model_calls(with_case):
    shell = with_case
    shell.build_mesh(nj=20, n_surface=30)
    out = shell.hand_off("paraview")
    assert out["launched"] is False and out["state"].endswith(".pvsm")
    line = shell.handoff_line(out)
    assert line.startswith("prepared: ") and "--state=" in line


def test_the_panel_never_opens_a_window_by_itself():
    """`launch` is not among the arguments any control builds. The panel
    prepares the handoff; a human presses the application's own icon, or asks
    for launch explicitly through the tool."""
    for control in actions.CONTROLS:
        try:
            args = control.build(case_id="wt_1")
        except (ValueError, TypeError):
            continue
        assert "launch" not in args, control.key


# -- formatting: the lane's laws, in the window ------------------------------


def test_a_result_is_never_shown_without_what_qualifies_it():
    line = WindTunnelShell.result_line(
        {
            "cl": 0.43,
            "cd": 0.011,
            "verdict": {"state": "converged"},
            "uncertainty": {"trust": "comparative"},
        }
    )
    assert "cl 0.43" in line and "[converged, comparative]" in line
    bare = WindTunnelShell.result_line({"cl": 0.43})
    assert "[?, ?]" in bare  # a number whose verdict is unknown says so


def test_a_status_line_stays_short_and_an_error_replaces_it():
    line = WindTunnelShell.status_line(
        {"state": "running", "iter": 120, "elapsed_s": 4.2, "coeffs": {"cl": 0.4, "cd": 0.01}}
    )
    assert line.startswith("running") and "iter 120" in line and len(line) < 80
    assert WindTunnelShell.status_line(
        {"error": "wt_unknown_run", "message": "no such run"}
    ).startswith("wt_unknown_run")


# -- Qt is an extra, and its absence is the tested case ----------------------


def test_importing_the_panel_loads_no_qt():
    """A fresh interpreter, because this suite's sys.modules is already dirty."""
    code = (
        "import sys;"
        "import tee.windtunnel.gui, tee.windtunnel.gui.actions, tee.windtunnel.gui.shell;"
        "import tee.windtunnel.gui.app;"
        "assert 'PySide6' not in sys.modules, sorted(m for m in sys.modules if 'Side' in m);"
        "print('clean')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-500:]
    assert "clean" in out.stdout


def test_the_window_names_the_extra_when_qt_is_absent():
    from tee.windtunnel.gui import app as gui_app

    try:
        import PySide6  # noqa: F401
    except ImportError:
        pass
    else:
        pytest.skip("PySide6 is installed here; the refusal cannot be observed")
    with pytest.raises(RuntimeError, match=r"tee-engine\[gui\]"):
        gui_app._require_qt()
    with pytest.raises(RuntimeError, match=r"tee-engine\[gui\]"):
        gui_app.main([])


def test_the_panel_adds_no_tool_to_the_surface(tmp_path):
    """A window is not a tool. The always-loaded surface is untouched by this
    package, and nothing in it is registered anywhere."""
    from tee.kernel import trust

    app = make_app(tmp_path)
    assert not [n for n in app.registry.names() if "gui" in n or "panel" in n]
    assert not [k for k in trust._EXPLICIT if "gui" in k or "panel" in k]
