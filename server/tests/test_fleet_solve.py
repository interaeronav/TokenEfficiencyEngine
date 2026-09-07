"""A45 P2a — the solver group, and the stdout guard the whole fleet needs.

The reference problem has a hand-checkable answer: maximise 3x+4y subject
to x+2y<=14 and 3x-y>=0 with 0<=x,y<=10. Optimum is 38 at x=10, y=2
(3*10+4*2 = 38; 10+2*2 = 14 exactly, so `cap` binds). All three engines
were verified to agree on this machine.
"""

from __future__ import annotations

import tempfile

import pytest

from tee.fleet import probe, solve
from tee.kernel.errors import TeeError

REF = {
    "sense": "max",
    "objective": {"x": 3, "y": 4},
    "variables": {"x": {"lb": 0, "ub": 10}, "y": {"lb": 0, "ub": 10}},
    "constraints": [
        {"name": "cap", "lhs": {"x": 1, "y": 2}, "op": "<=", "rhs": 14},
        {"name": "ratio", "lhs": {"x": 3, "y": -1}, "op": ">=", "rhs": 0},
    ],
}

has_pulp = pytest.mark.skipif(not probe.have("pulp"), reason="[solve] extra not installed")


# -- the guard --------------------------------------------------------------


def test_native_stdout_is_captured_at_the_fd_level():
    """`contextlib.redirect_stdout` does NOT stop native code - it rebinds a
    Python object while C++ writes to fd 1. Measured: the OR-Tools HiGHS
    banner (92 bytes) escaped redirect_stdout entirely. os.dup2 is the only
    thing that holds, and TEE speaks JSON-RPC over that exact descriptor."""
    import os

    from tee.fleet.quiet import muted_stdout

    with muted_stdout() as sink:
        os.write(1, b"raw bytes straight to fd 1\n")
    assert "raw bytes straight to fd 1" in sink.text


def test_the_guard_restores_stdout_even_when_the_body_raises():
    import os

    from tee.fleet.quiet import muted_stdout

    before = os.dup(1)
    try:
        with pytest.raises(ValueError), muted_stdout():
            raise ValueError("boom")
        os.write(1, b"")  # fd 1 is still usable
    finally:
        os.close(before)


@has_pulp
def test_a_real_solve_emits_nothing_on_stdout(capfd):
    """The end-to-end property: no fleet call may pollute the protocol."""
    solve.solve(dict(REF, backend="highs"))
    out, _ = capfd.readouterr()
    assert out == "", f"stdout polluted with {out!r}"


# -- correctness ------------------------------------------------------------


@has_pulp
@pytest.mark.parametrize("backend", ["highs", "scip", "cbc"])
def test_every_backend_agrees_on_the_reference_optimum(backend):
    r = solve.solve(dict(REF, backend=backend))
    assert r["status"] == "optimal"
    assert r["objective"] == pytest.approx(38.0)
    assert r["nonzero"]["x"] == pytest.approx(10.0)
    assert r["nonzero"]["y"] == pytest.approx(2.0)
    assert "cap" in r["binding"], "x+2y=14 is tight at the optimum"


@has_pulp
def test_integer_variables_make_it_a_mip():
    spec = dict(REF)
    spec["variables"] = {"x": {"lb": 0, "ub": 10, "type": "int"}, "y": {"lb": 0, "ub": 10}}
    r = solve.solve(spec)
    assert r["status"] == "optimal"
    assert float(r["nonzero"]["x"]).is_integer()


@has_pulp
def test_infeasible_answers_with_a_fix_not_a_crash():
    spec = dict(REF)
    spec["constraints"] = REF["constraints"] + [
        {"name": "impossible", "lhs": {"x": 1}, "op": ">=", "rhs": 99}
    ]
    r = solve.solve(spec)
    assert r["ok"] is False
    assert r["status"] == "infeasible"
    assert "constraint" in r["fix"].lower()


# -- token discipline -------------------------------------------------------


@has_pulp
def test_a_large_solution_is_summarised_not_dumped():
    """The whole point. 400 variables must not become 400 lines."""
    n = 400
    spec = {
        "sense": "max",
        "objective": {f"v{i}": 1 for i in range(n)},
        "variables": {f"v{i}": {"lb": 0, "ub": 1} for i in range(n)},
        "constraints": [
            {"name": "budget", "lhs": {f"v{i}": 1 for i in range(n)}, "op": "<=", "rhs": 250}
        ],
    }
    r = solve.solve(spec)
    assert r["status"] == "optimal"
    assert r["n_nonzero"] == 250
    assert len(r["nonzero"]) == solve.DEFAULT_SHOW, "must truncate to the show budget"
    assert "solve_detail" in r["note"]
    # and the full vector is reachable, on purpose, by a second call
    page = solve.detail(r["solution_id"], offset=0, limit=500)
    assert page["total"] == n
    assert page["returned"] == 400


@has_pulp
def test_detail_pages_and_can_return_the_engine_log():
    r = solve.solve(dict(REF, backend="highs"))
    p = solve.detail(r["solution_id"], offset=1, limit=1)
    assert p["returned"] == 1 and p["offset"] == 1
    log = solve.detail(r["solution_id"], log=True)
    assert "solver_log" in log


def test_unknown_solution_id_refuses_with_the_known_ids():
    with pytest.raises(TeeError) as e:
        solve.detail("sol_nope")
    assert "No solution" in e.value.message


# -- CP-SAT -----------------------------------------------------------------


@pytest.mark.skipif(not probe.have("ortools"), reason="ortools not installed")
def test_cpsat_solves_a_knapsack_with_a_hand_checked_answer():
    """capacity 4; a=(w3,v5) b=(w2,v3) c=(w2,v4). b+c = w4 v7 beats a = v5."""
    r = solve.cpsat(
        {
            "sense": "max",
            "objective": {"a": 5, "b": 3, "c": 4},
            "variables": {n: {"lb": 0, "ub": 1} for n in "abc"},
            "constraints": [
                {"name": "weight", "lhs": {"a": 3, "b": 2, "c": 2}, "op": "<=", "rhs": 4}
            ],
        }
    )
    assert r["status"] == "optimal"
    assert r["objective"] == pytest.approx(7.0)
    assert r["nonzero"] == {"b": 1, "c": 1}


# -- refusal + registration -------------------------------------------------


def test_a_missing_extra_refuses_with_the_exact_command():
    with pytest.raises(TeeError) as e:
        probe.need("definitely_not_installed_xyz", "solve", what="the thing")
    assert "tee-engine[solve]" in e.value.fix
    assert "not installed" in e.value.message


def test_bad_specs_are_refused_before_any_solver_runs():
    for spec, expect in (
        ({"variables": {}}, "No variables"),
        ({"sense": "sideways", "variables": {"x": {}}}, "not min or max"),
        ({"variables": {"x": {"type": "complex"}}}, "unknown"),
        ({"variables": {"x": {}}, "objective": {"ghost": 1}}, "undeclared"),
    ):
        with pytest.raises(TeeError) as e:
            solve.solve(spec)
        assert expect in e.value.message, f"{spec} -> {e.value.message}"


def test_bad_cpsat_specs_are_refused_before_ortools_is_needed():
    """Rule 6 for the CP-SAT lane: an argument the caller can fix right now
    comes before a dependency they would have to install. Deliberately NOT
    gated on `probe.have("ortools")` - the whole claim is that these refusals
    land on a machine where the [solve] extra was never installed, so a test
    that only runs where it IS installed would prove nothing.

    This is also the list that makes `_cpsat_worker`'s own checks redundant:
    every refusal the worker can make appears here, in the parent."""
    for spec, expect in (
        ({"variables": {}}, "No variables declared."),
        ({"sense": "sideways", "variables": {"x": {}}}, "not min or max"),
        ({"variables": {"x": {"type": "complex"}}}, "type 'complex' is unknown"),
        ({"variables": {"x": {}}, "objective": {"ghost": 1}}, "undeclared"),
        (
            {"variables": {"x": {}}, "constraints": [{"lhs": {"ghost": 1}, "op": "<="}]},
            "constraint 0 names undeclared variables: ['ghost']",
        ),
        (
            {"variables": {"x": {}}, "constraints": [{"lhs": {"x": 1}, "op": "!="}]},
            "op '!=' is unknown",
        ),
    ):
        with pytest.raises(TeeError) as e:
            solve.cpsat(spec)
        assert e.value.code == "solve_bad_spec", f"{spec} -> {e.value.code}"
        assert expect in e.value.message, f"{spec} -> {e.value.message}"


def test_cpsat_refuses_a_continuous_variable_instead_of_integerising_it():
    """The one rule `_check` cannot share between the lanes. CP-SAT has no
    continuous domain, so honouring `type: "cont"` is not an option and
    ignoring it is a different answer, silently - the worse of the two."""
    with pytest.raises(TeeError) as e:
        solve.cpsat({"variables": {"x": {"lb": 0, "ub": 10, "type": "cont"}}})
    assert "continuous" in e.value.message
    assert "solve_program" in e.value.fix, "must name the lane that CAN do it"


def test_cpsat_refuses_a_fractional_bound_instead_of_truncating_it():
    """Same defect wearing different clothes: the worker's `int(ub)` turns
    2.5 into 2 and answers as if that was asked for."""
    with pytest.raises(TeeError) as e:
        solve.cpsat({"variables": {"x": {"lb": 0, "ub": 2.5}}})
    assert "whole number" in e.value.message


def test_an_omitted_type_is_an_integer_in_the_cpsat_lane_not_a_refusal():
    """`cont` is the LP default, and inheriting it here would refuse every
    CP-SAT spec in this file. An omitted field is not a request."""
    checked = solve._check({"variables": {"x": {"lb": 0, "ub": 1}}}, integer_only=True)
    assert checked.variables == {"x": {"lb": 0, "ub": 1}}
    assert checked.sense == "min"


def test_the_cpsat_lane_does_not_refuse_the_backend_name_its_probe_advertises():
    """`solve_backends` reports "cp-sat" as a ready backend, so a model will
    hand it straight back. `_require_backend` knows only highs/scip/cbc and
    would refuse it as not a backend - which is why this lane never consults
    the field. Running the LP check on a CP-SAT spec would be a new bug."""
    checked = solve._check({"variables": {"x": {}}, "backend": "cp-sat"}, integer_only=True)
    assert checked.backend == "cp-sat"
    with pytest.raises(TeeError) as e:
        solve._check({"variables": {"x": {}}, "backend": "cp-sat"})
    assert e.value.code == "solve_bad_backend", "the LP lane still refuses it, on purpose"


@pytest.mark.skipif(not probe.have("ortools"), reason="ortools not installed")
def test_a_binary_variable_is_binary_in_the_cpsat_lane():
    """`type` used to be read by nobody: every variable became IntVar(lb, ub)
    with ub defaulting to 100, so this exact spec answered x=100."""
    r = solve.cpsat({"sense": "max", "objective": {"x": 1}, "variables": {"x": {"type": "bin"}}})
    assert r["status"] == "optimal"
    assert r["nonzero"] == {"x": 1}


@pytest.mark.skipif(not probe.have("ortools"), reason="ortools not installed")
def test_the_worker_names_an_undeclared_variable_in_the_parents_words():
    """The parent now refuses this before the worker is spawned, so the only
    way to reach the worker's copy is by path - which the module supports on
    purpose. Redundant is fine; contradicting is not, so the two must answer
    the same. It used to answer {"error": "KeyError", "message": "'ghost'"}."""
    import json as _json
    import subprocess
    import sys
    from pathlib import Path

    from tee.fleet import solve as _s

    spec = {"variables": {"x": {"lb": 0, "ub": 5}}, "constraints": [{"lhs": {"ghost": 1}}]}
    p = subprocess.run(
        [sys.executable, str(Path(_s.__file__).parent / "_cpsat_worker.py")],
        input=_json.dumps(spec),
        capture_output=True,
        text=True,
        timeout=120,
    )
    from_worker = _json.loads(p.stdout)["message"]

    with pytest.raises(TeeError) as e:
        solve.cpsat(spec)
    assert from_worker == e.value.message == "constraint 0 names undeclared variables: ['ghost']"


def test_tools_register_on_the_read_compute_capability():
    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    for name in ("solve_program", "solve_cpsat", "solve_detail", "solve_backends"):
        assert name in app.registry._tools, name
        assert app.registry._tools[name].capability == "read-compute"


def test_backends_probe_names_the_install_line_when_empty(monkeypatch):
    monkeypatch.setattr(probe, "have", lambda mod: False)
    r = solve.backends()
    assert r["ready"] == []
    assert "tee-engine[solve]" in r["fix"]


@pytest.mark.skipif(not probe.have("ortools"), reason="ortools not installed")
@has_pulp
def test_cpsat_survives_highspy_already_being_loaded():
    """The regression this subprocess exists for. In-process, importing
    highspy first makes `from ortools.sat.python import cp_model` raise
    ImportError (each ships a different libhighs and the linker binds to
    whichever loaded first). Isolation must make tool ORDER irrelevant."""
    import highspy  # noqa: F401 - loading it is the point

    solve.solve(dict(REF, backend="highs"))  # and actually use it
    r = solve.cpsat(
        {
            "sense": "max",
            "objective": {"a": 5, "b": 3, "c": 4},
            "variables": {n: {"lb": 0, "ub": 1} for n in "abc"},
            "constraints": [
                {"name": "weight", "lhs": {"a": 3, "b": 2, "c": 2}, "op": "<=", "rhs": 4}
            ],
        }
    )
    assert r["status"] == "optimal"
    assert r["objective"] == pytest.approx(7.0)


@pytest.mark.skipif(not probe.have("ortools"), reason="ortools not installed")
def test_the_cpsat_worker_returns_only_json_on_stdout():
    """Its whole contract: one JSON object, never a solver banner."""
    import json as _json
    import subprocess
    import sys
    from pathlib import Path

    from tee.fleet import solve as _s

    worker = Path(_s.__file__).parent / "_cpsat_worker.py"
    spec = {"variables": {"x": {"lb": 0, "ub": 5}}, "objective": {"x": 1}, "sense": "max"}
    p = subprocess.run(
        [sys.executable, str(worker)],
        input=_json.dumps(spec),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert p.returncode == 0
    payload = _json.loads(p.stdout)  # raises if anything else was printed
    assert payload["values"]["x"] == 5
