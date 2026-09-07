"""A75 P1: the fd_* surface, exercised with JSBSim ABSENT wherever it can be.

The lane's whole deterministic half - generating an aircraft, refusing a bad
polar, naming a missing engine - must work on a machine that cannot fly, and a
test that only passes where jsbsim happens to be installed would not prove it.
The live tier is marked `fdm`.
"""

from __future__ import annotations

import importlib
import json
import sys

import pytest

from tee.app import TeeApp
from tee.flightdyn import aircraft as ac
from tee.flightdyn.tools import register_flightdyn_tools
from tee.kernel import trust
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.server import _DESC

FD_TOOLS = ["fd_aircraft", "fd_fly", "fd_modes", "fd_probe", "fd_trim"]

POLAR = {
    "alpha_deg": [-6.0, -3.0, 0.0, 3.0, 6.0, 9.0, 12.0, 15.0],
    "cl": [-0.38, -0.06, 0.26, 0.58, 0.89, 1.18, 1.40, 1.32],
    "cd": [0.0181, 0.0132, 0.0121, 0.0148, 0.0213, 0.0316, 0.0470, 0.0721],
    "cm_alpha": -0.55,
    "cm_q": -12.0,
    "cm_de": -1.1,
    "source": "test fixture",
}
MASS = {"mass_kg": 850.0, "ixx": 1290.0, "iyy": 1820.0, "izz": 2670.0}
GEOM = {"wing_area_m2": 16.2, "span_m": 10.9, "chord_m": 1.49}


@pytest.fixture
def app(tmp_path):
    a = TeeApp({"fake": FakeAdapter()})
    register_flightdyn_tools(a, tmp_path)
    return a


def call(app_, tool, /, **args):
    """Positional `app_`: a keyword `app` collides with tool arguments, a trap
    A73 hit twice in one campaign."""
    return app_.registry.call(tool, args)


class _Blocker:
    """Make a module invisible to BOTH find_spec and import_module.

    Blocking only one half makes the skip markers lie about what was tested.
    """

    def __init__(self, name):
        self.name = name

    def find_spec(self, fullname, path=None, target=None):
        if fullname == self.name or fullname.startswith(self.name + "."):
            raise ImportError(f"{fullname} is blocked by the test")
        return None


@pytest.fixture
def no_jsbsim(monkeypatch):
    for mod in [m for m in list(sys.modules) if m == "jsbsim" or m.startswith("jsbsim.")]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    blocker = _Blocker("jsbsim")
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])
    importlib.invalidate_caches()
    yield


# --- the surface ---------------------------------------------------------


def test_the_lane_registers_exactly_its_tools(app):
    assert sorted(n for n in app.registry.names() if n.startswith("fd_")) == FD_TOOLS


def test_the_always_loaded_surface_did_not_move(app):
    assert len(_DESC) == 17, "the always-loaded surface moved"
    assert not [n for n in _DESC if n.startswith("fd_")], "an fd_ tool leaked onto the surface"


def test_every_registered_tool_is_tabled_in_the_trust_kernel(app):
    for name in FD_TOOLS:
        assert trust.capability_for(name) in trust.CAPABILITIES


def test_there_is_no_fd_family_row():
    assert not [p for p, _ in trust._FAMILY if p == "fd_"], (
        "a family row would silently admit whatever fd_ tool is named next"
    )


def test_an_untabled_fd_tool_is_a_startup_error():
    with pytest.raises(TeeError) as e:
        trust.capability_for("fd_not_in_the_table")
    assert e.value.code == "trust_untabled_tool"


@pytest.mark.parametrize(
    "query,expected",
    [
        ("flight dynamics", "fd_aircraft"),
        ("phugoid", "fd_modes"),
        ("trim an aircraft", "fd_trim"),
        ("dynamic modes of an aeroplane", "fd_modes"),
    ],
)
def test_search_reaches_the_lane_by_capability_words(app, query, expected):
    top = [i["name"] for i in app.registry.search(query)["items"][:3]]
    assert expected in top, f"{query!r} did not reach {expected}: {top}"


def test_the_lane_does_not_claim_another_lanes_search_words(app):
    forbidden = {"mesh", "drawing", "image", "document", "cloud"}
    for name in FD_TOOLS:
        d = app.registry.describe(name)
        words = set((name + " " + " ".join(d.get("tags", []))).lower().split())
        assert not (words & forbidden), f"{name} claims another lane's words"


# --- the generator, with no engine anywhere in sight ---------------------


def test_generating_an_aircraft_needs_no_jsbsim(app, no_jsbsim, tmp_path):
    out = call(
        app,
        "fd_aircraft",
        action="create",
        aircraft_id="demo",
        polar=POLAR,
        mass=MASS,
        geometry=GEOM,
    )
    assert out["polar_points"] == 8
    assert out["max_thrust_n"] > 0
    xml = (tmp_path / ".tee" / "flightdyn" / "demo" / "aircraft" / "demo" / "demo.xml").read_text()
    assert 'unit="M2"' in xml and 'unit="KG*M2"' in xml, "SI units go on the wire"
    assert "generated-by TEE" in xml
    # the turbine's two function tables are NOT optional: without them JSBSim
    # segfaults at run_ic rather than reporting a problem.
    eng = (tmp_path / ".tee" / "flightdyn" / "demo" / "engine" / "tee_thrust.xml").read_text()
    assert 'name="IdleThrust"' in eng and 'name="MilThrust"' in eng


def test_show_and_list_round_trip(app):
    call(
        app,
        "fd_aircraft",
        action="create",
        aircraft_id="demo",
        polar=POLAR,
        mass=MASS,
        geometry=GEOM,
    )
    assert call(app, "fd_aircraft", action="list")["aircraft"] == ["demo"]
    assert call(app, "fd_aircraft", action="show", aircraft_id="demo")["polar_points"] == 8


@pytest.mark.parametrize(
    "bad,code",
    [
        ({"alpha_deg": [0.0], "cl": [0.1], "cd": [0.01]}, "fd_polar_short"),
        ({"alpha_deg": [0.0, 3.0], "cl": [0.1], "cd": [0.01]}, "fd_polar_ragged"),
        ({"alpha_deg": [3.0, 0.0], "cl": [0.1, 0.2], "cd": [0.01, 0.02]}, "fd_polar_unsorted"),
    ],
)
def test_a_bad_polar_is_refused_by_name(app, bad, code):
    with pytest.raises(TeeError) as e:
        call(
            app,
            "fd_aircraft",
            action="create",
            aircraft_id="bad",
            polar=bad,
            mass=MASS,
            geometry=GEOM,
        )
    assert e.value.code == code
    assert e.value.fix


def test_a_zero_inertia_is_not_an_aircraft(app):
    with pytest.raises(TeeError) as e:
        call(
            app,
            "fd_aircraft",
            action="create",
            aircraft_id="bad",
            polar=POLAR,
            mass={"mass_kg": 850.0, "ixx": 0.0, "iyy": 1820.0, "izz": 2670.0},
            geometry=GEOM,
        )
    assert e.value.code == "fd_mass_nonpositive"


def test_an_unknown_aircraft_is_refused_with_the_known_ids(app):
    call(
        app,
        "fd_aircraft",
        action="create",
        aircraft_id="demo",
        polar=POLAR,
        mass=MASS,
        geometry=GEOM,
    )
    with pytest.raises(TeeError) as e:
        call(app, "fd_trim", aircraft_id="nope")
    assert e.value.code == "fd_no_aircraft" and "demo" in e.value.message


def test_thrust_is_sized_from_the_polar_not_guessed():
    p = ac.Polar(tuple(POLAR["alpha_deg"]), tuple(POLAR["cl"]), tuple(POLAR["cd"]))
    m, g = ac.Mass(850.0, 1290.0, 1820.0, 2670.0), ac.Geometry(16.2, 10.9, 1.49)
    light = ac.size_thrust_n(p, m, g, ac.Design())
    heavy = ac.size_thrust_n(p, ac.Mass(1700.0, 1290.0, 1820.0, 2670.0), g, ac.Design())
    assert heavy > light, "a heavier aeroplane needs more thrust to hold level"
    assert 100.0 < light < 5000.0, f"{light} N is not a sane thrust for this aeroplane"


# --- the live tier -------------------------------------------------------


@pytest.mark.fdm
def test_a_generated_aircraft_trims_and_its_modes_are_physical(app):
    """P3's acceptance criterion: OUR aircraft, not a bundled one."""
    pytest.importorskip("jsbsim")
    call(
        app,
        "fd_aircraft",
        action="create",
        aircraft_id="demo",
        polar=POLAR,
        mass=MASS,
        geometry=GEOM,
    )
    out = call(app, "fd_modes", aircraft_id="demo", condition={"altitude_ft": 5000.0, "kcas": 90.0})
    trim = out["trim"]
    assert trim["converged"] and trim["iterations"] < 30
    assert abs(trim["gamma_deg"]) < 0.05, "level trim must be level"
    assert 0.0 < trim["throttle"] < 1.0

    modes = out["modes"]["modes"]
    names = [" ".join(m["participation"]) for m in modes]
    sp = [m for m, n in zip(modes, names, strict=True) if "Alpha" in n and "Q" in n]
    ph = [m for m, n in zip(modes, names, strict=True) if "Vt" in n and "Theta" in n]
    assert sp, f"no short period among {names}"
    assert ph, f"no phugoid among {names}"
    assert 0.2 < sp[0]["zeta"] < 1.5, "short-period damping is not physical"
    assert ph[0]["period_s"] > 5 * sp[0]["period_s"], "the phugoid is the slow one"

    # the closed-form witness. These approximations neglect thrust and are
    # worth roughly a factor, not a percent - so the band is stated, not tight.
    chk = out["modes"]["cross_check"]
    assert abs(chk["period_error_pct"]) < 60.0, chk
    assert 0.3 < chk["phugoid_zeta"] / chk["zeta_theory"] < 3.0, chk
    assert 5.0 < chk["lift_over_drag"] < 60.0, chk


@pytest.mark.fdm
def test_the_trim_holds_when_it_is_flown(app):
    pytest.importorskip("jsbsim")
    call(
        app,
        "fd_aircraft",
        action="create",
        aircraft_id="demo",
        polar=POLAR,
        mass=MASS,
        geometry=GEOM,
    )
    out = call(app, "fd_fly", aircraft_id="demo", seconds=60.0)
    hold = out["hold"]
    assert abs(hold["altitude_drift_ft"]) < 50.0, hold
    assert abs(hold["kcas"] - 90.0) < 2.0, hold
    assert abs(hold["nz"] - 1.0) < 0.05, hold


@pytest.mark.fdm
def test_the_reply_is_a_digest_not_a_history(app):
    pytest.importorskip("jsbsim")
    call(
        app,
        "fd_aircraft",
        action="create",
        aircraft_id="demo",
        polar=POLAR,
        mass=MASS,
        geometry=GEOM,
    )
    out = call(app, "fd_modes", aircraft_id="demo")
    blob = json.dumps(out)
    assert len(blob) < 4000, f"the reply grew to {len(blob)} bytes"

    def walk(o):
        if isinstance(o, list):
            assert len(o) <= 64, f"an array of {len(o)} escaped the digest"
            for v in o:
                walk(v)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, str):
            assert len(o) <= 2048

    walk(out)


def test_the_probe_asks_the_running_interpreter_not_the_path():
    """A bare `python` is a different interpreter under a bundled venv, and the
    probe would report the wheel absent on a machine that has it. Caught by
    booting the real bundle, which said present=False with jsbsim installed."""
    src = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src"
        / "tee"
        / "flightdyn"
        / "probe.py"
    ).read_text()
    assert "sys.executable" in src
    assert '["python"' not in src and '"python", "-c"' not in src
