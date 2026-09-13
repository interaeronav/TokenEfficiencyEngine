"""Structural acceptance: analytic controls, native engines, state and process boundaries."""

import copy
import json
import math
import os
import sys
import threading
import time
from pathlib import Path

import pytest

from tee.kernel.errors import TeeError
from tee.structural import mechanics, runner
from tee.structural.decks import write_aster
from tee.structural.environment import assess
from tee.structural.examples import cantilever
from tee.structural.model import StructuralError, validate
from tee.structural.service import StructuralService


def test_explicit_inputs_and_units():
    m = cantilever()
    assert validate(m) == m
    for mutate in [
        lambda x: x.update(units="kN-m"),
        lambda x: x["materials"][0].update(E_mpa=0),
        lambda x: x["materials"][0].update(nu=0.5),
        lambda x: x["nodes"][1].update(xy_mm=[True, 0]),
        lambda x: x["elements"][0].update(nodes=["tip", "tip"]),
        lambda x: x["materials"][0].pop("alpha_per_c"),
        lambda x: x["cases"][0]["nodal"][0].update(fy_n=float("nan")),
        lambda x: x["sections"][0].update(source=""),
        lambda x: x["supports"][0].update(fixed=[1, 1, 1]),
        lambda x: x["combinations"][0]["factors"].update(absent=1),
        lambda x: x.update(arbitrary_python="bad"),
    ]:
        bad = copy.deepcopy(m)
        mutate(bad)
        with pytest.raises(StructuralError):
            validate(bad)


def test_stability_checks_true_mechanism_and_not_merely_support_count():
    m = cantilever()
    m["supports"][0]["fixed"] = [True, True, False]
    with pytest.raises(StructuralError, match="Unstable"):
        mechanics.system(validate(m))
    m = cantilever()
    m["supports"][0]["fixed"] = [True, False, False]
    m["supports"].append({"node": "tip", "fixed": [False, True, True], "source": "test"})
    assert mechanics.system(validate(m))["scaled_condition"] > 0


def test_revision_staleness_and_read_tier(tmp_path):
    s = StructuralService(tmp_path)
    assert runner.scan({"oofem": "/missing"})["engines"][1]["state"] == "missing"
    assert not s.root.exists()
    a = s.save(cantilever())
    b = s.save(cantilever(), a["model_id"], 1)
    assert b["revision"] == 2
    with pytest.raises(StructuralError, match="Stale"):
        s.save(cantilever(), a["model_id"], 1)
    with pytest.raises(StructuralError, match="Stale"):
        s.solve(a["model_id"], 1, "vertical", "openseespy", threading.Event())
    p = s.query(a["model_id"], "nodes", 1, 1)
    assert p["rows"][0]["id"] == "tip"
    with pytest.raises(StructuralError):
        s.query(a["model_id"], "nodes", False, 1)
    folder = s.folder(a["model_id"])
    rec = json.loads((folder / "model.json").read_text())
    rec["model"]["name"] = "changed"
    (folder / "model.json").write_text(json.dumps(rec))
    with pytest.raises(StructuralError, match="checksum"):
        s.state(a["model_id"])


def test_symlink_refusal(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (tmp_path / ".tee").mkdir()
    (tmp_path / ".tee/structural").symlink_to(target)
    with pytest.raises(StructuralError, match="symbolic"):
        StructuralService(tmp_path).save(cantilever())
    assert not list(target.iterdir())


def test_cancel_terminates_owned_solver_process(tmp_path):
    script = tmp_path / "slow.py"
    script.write_text(
        "import os,time\nfrom pathlib import Path\n"
        'Path("pid").write_text(str(os.getpid()))\ntime.sleep(60)\n'
    )
    stop = threading.Event()
    errors = []

    def work():
        try:
            runner.execute([sys.executable, str(script)], tmp_path, stop, 10)
        except StructuralError as e:
            errors.append(str(e))

    t = threading.Thread(target=work)
    t.start()
    deadline = time.monotonic() + 5
    while not (tmp_path / "pid").exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert (tmp_path / "pid").exists()
    pid = int((tmp_path / "pid").read_text())
    stop.set()
    t.join(3)
    assert not t.is_alive() and "cancelled" in errors[0]
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_solver_failure_and_timeout_are_not_results(tmp_path):
    for name, code, timeout in [
        ("fail", "raise SystemExit(2)", 2),
        ("timeout", "import time;time.sleep(5)", 0.05),
    ]:
        p = tmp_path / name
        p.mkdir()
        script = p / "worker.py"
        script.write_text(code)
        with pytest.raises(StructuralError):
            runner.execute([sys.executable, str(script)], p, threading.Event(), timeout)


def test_code_aster_two_launchers_and_no_invented_section(tmp_path):
    m = validate(cantilever())
    s = mechanics.system(m)
    loads = mechanics.loading(m, s, "vertical")
    for launcher in ["as_run", "run_aster"]:
        p = tmp_path / launcher
        p.mkdir()
        files = write_aster(p, m, loads, launcher)
        assert len(files) == 3
        compile((p / "analysis.comm").read_text(), "analysis.comm", "exec")
        assert "POU_D_T" in (p / "analysis.comm").read_text()
        assert ("P memjob" in (p / "analysis.export").read_text()) == (launcher == "as_run")
    m["sections"][0].pop("iy_mm4")
    with pytest.raises(StructuralError, match="iy_mm4"):
        write_aster(tmp_path, m, loads, "as_run")


def test_harsh_environment_missing_evidence_stays_unknown():
    a = assess(
        exposures=[
            {"mechanism": "chloride_corrosion", "status": "present", "source": "site water report"}
        ],
        limit=50,
    )
    assert a["service_life_years"] is None and a["strength_reduction_factor"] is None
    rows = {r["id"]: r for r in a["rows"]}
    assert rows["chloride_corrosion"]["reported_exposure"]["status"] == "present"
    assert rows["chloride_corrosion"]["damage_status"] == "not_assessed"
    assert rows["sulfate_attack"]["reported_exposure"]["status"] == "unknown"
    assert len(assess("software", limit=50)["rows"]) >= 11
    with pytest.raises(StructuralError):
        assess(exposures=[{"mechanism": "sulfate_attack", "status": "present", "source": ""}])


def run_live(tmp_path, m, engine, case):
    if os.environ.get("TEE_STRUCTURAL_LIVE") != "1":
        pytest.skip("explicit real-engine integration gate")
    if runner.executable(engine, {})[0] is None:
        pytest.fail(f"{engine} requested but missing")
    s = StructuralService(tmp_path)
    a = s.save(m)
    r = s.solve(a["model_id"], 1, case, engine, threading.Event())
    result = json.loads((Path(r["evidence_path"]) / "result.json").read_text())
    return s, a, r, result["result"]


@pytest.mark.parametrize("engine", ["openseespy", "oofem"])
@pytest.mark.parametrize("case", ["vertical", "axial", "heat", "udl", "combined"])
def test_native_analytic_controls(tmp_path, engine, case):
    m = cantilever()
    s, a, r, v = run_live(tmp_path, m, engine, case)
    length = 3000.0
    e = 200000.0
    area = 6000.0
    inertia = 200e6
    ga = e / (2 * 1.3) * 5000.0
    vertical = -10000 * length**3 / (3 * e * inertia) - 10000 * length / ga
    vals = {
        "vertical": [0, vertical, -10000 * length**2 / (2 * e * inertia)],
        "axial": [10000 * length / (e * area), 0, 0],
        "heat": [12e-6 * 40 * length, 0, 0],
        "udl": [
            0,
            -3 * length**4 / (8 * e * inertia) - 3 * length**2 / (2 * ga),
            -3 * length**3 / (6 * e * inertia),
        ],
        "combined": [1.5 * 0.025 + 1.44, 1.2 * vertical, 1.2 * (-0.001125)],
    }
    assert v["displacements"]["tip"] == pytest.approx(vals[case], rel=1e-7, abs=1e-9)
    assert r["checks"]["passed"] and r["capacity_status"] == "not_assessed"
    if case == "heat":
        assert max(abs(x) for x in v["element_forces"]["beam"]) < 1e-5
    s.save(m, a["model_id"], 1)
    assert s.result(a["model_id"], r["run_id"])["stale"]


@pytest.mark.parametrize("engine", ["openseespy", "oofem"])
def test_native_rotated_cantilever(tmp_path, engine):
    m = cantilever()
    theta = 0.673
    c = math.cos(theta)
    sn = math.sin(theta)
    m["nodes"][1]["xy_mm"] = [3000 * c, 3000 * sn]
    load = m["cases"][0]["nodal"][0]
    load["fx_n"] = 10000 * sn
    load["fy_n"] = -10000 * c
    _, _, _, v = run_live(tmp_path, m, engine, "vertical")
    assert v["displacements"]["tip"] == pytest.approx(
        [2.328 * sn, -2.328 * c, -0.001125], rel=1e-7, abs=1e-9
    )


@pytest.mark.parametrize("engine", ["openseespy", "oofem"])
def test_native_restrained_heat_and_moment(tmp_path, engine):
    m = cantilever()
    m["supports"].append(
        {"node": "tip", "fixed": [True, False, False], "source": "synthetic longitudinal restraint"}
    )
    _, _, _, v = run_live(tmp_path, m, engine, "heat")
    assert v["element_forces"]["beam"] == pytest.approx([576000, 0, 0, -576000, 0, 0], abs=1e-4)
    assert v["reactions"]["base"][0] == pytest.approx(576000)


def test_native_result_critic_rejects_false_force_and_truncated_output(tmp_path):
    m = cantilever()
    _, _, r, _v = run_live(tmp_path, m, "openseespy", "vertical")
    raw = json.loads((Path(r["evidence_path"]) / "solver-result.json").read_text())
    s = mechanics.system(m)
    loads = mechanics.loading(m, s, "vertical")
    for mutate in [
        lambda x: x["displacements"].pop("tip"),
        lambda x: x["element_forces"]["beam"].__setitem__(0, 100),
        lambda x: x["displacements"]["base"].__setitem__(0, 1),
        lambda x: x["reactions"]["base"].__setitem__(1, float("nan")),
    ]:
        bad = copy.deepcopy(raw)
        mutate(bad)
        with pytest.raises(StructuralError):
            mechanics.check(m, s, loads, bad)


def test_tee_tools_discovery_and_jobs(tmp_path):
    from tee.app import TeeApp
    from tee.kernel import trust, trustctx
    from tee.kernel.adapter import FakeAdapter
    from tee.structural.tools import register_structural_tools

    trustctx.install("live-turn", ())
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        register_structural_tools(app, tmp_path)
        m = app.registry.call("st_status", {"detail": "example"})["model"]
        a = app.registry.call("st_model", {"model": m})
        assert app.registry.call("st_query", {"model_id": a["model_id"]})["revision"] == 1
        assert trust.capability_for("st_solve") == "call-engine"
        assert app.registry.call("st_environment", {})["service_life_years"] is None
        assert not list(app.structural.folder(a["model_id"]).glob("run_*"))
        with pytest.raises(TeeError):
            app.registry.call("st_query", {"model_id": a["model_id"], "limit": 0})
    finally:
        app.shutdown()
        trustctx.install("content-derived", ())


def test_bim_link_is_geometric_explicit_and_revision_checked(tmp_path):
    from tee.architecture.service import ArchitectureService

    a = ArchitectureService(tmp_path)
    mid = a.create("BIM structure fixture")["model_id"]
    s = StructuralService(tmp_path)
    operations = [
        {
            "op": "create",
            "entity": {
                "id": "ground",
                "kind": "storey",
                "name": "Ground",
                "elevation": 1000,
                "height": 3000,
            },
        },
        {
            "op": "create",
            "entity": {
                "id": "beam",
                "kind": "member",
                "name": "Test beam",
                "storey": "ground",
                "role": "beam",
                "origin": [100, 200, 300],
                "axis": [1, 0, 0],
                "x_direction": [0, 1, 0],
                "length": 3000,
                "profile": [[0, 0], [100, 0], [100, 200], [0, 200]],
            },
        },
    ]
    a.edit(mid, operations, expected_revision=0)
    candidate = s.from_bim(mid, ["beam"])
    row = candidate["members"][0]
    assert row["centroid_axis_start_mm"] == [100, 250, 1400]
    assert row["centroid_axis_end_mm"] == [3100, 250, 1400]
    assert row["geometric_area_mm2"] == 20000
    assert not candidate["automatically_merged_nodes"]
    assert candidate["page"] == {"offset": 0, "returned": 1, "total": 1, "next_offset": None}
    assert s.from_bim(mid, ["beam"], 1, 1)["members"] == []
    with pytest.raises(StructuralError, match="offset"):
        s.from_bim(mid, ["beam"], False, 1)
    m = cantilever()
    m["bim_source"] = candidate["bim_source"]
    s.check_bim(validate(m))
    a.edit(mid, [{"op": "update", "id": "beam", "changes": {"length": 3001}}], expected_revision=1)
    with pytest.raises(StructuralError, match="changed"):
        s.check_bim(m)


@pytest.mark.parametrize("engine", ["openseespy", "oofem"])
def test_native_portal_frame(tmp_path, engine):
    m = cantilever()
    src = "Synthetic portal, not a code wind load."
    m["nodes"] = [
        {"id": "a", "xy_mm": [0, 0]},
        {"id": "b", "xy_mm": [0, 3000]},
        {"id": "c", "xy_mm": [5000, 3000]},
        {"id": "d", "xy_mm": [5000, 0]},
    ]
    m["elements"] = [
        {"id": ident, "nodes": ends, "material": "test", "section": "test", "source": src}
        for ident, ends in [("left", ["a", "b"]), ("top", ["b", "c"]), ("right", ["d", "c"])]
    ]
    m["supports"] = [{"node": i, "fixed": [True, True, True], "source": src} for i in ["a", "d"]]
    m["cases"] = [
        {
            "id": "lateral",
            "source": src,
            "nodal": [{"node": "b", "fx_n": 17003, "fy_n": -301, "mz_nmm": 11303, "source": src}],
        }
    ]
    m["combinations"] = []
    _, _, _, v = run_live(tmp_path, m, engine, "lateral")
    assert len(v["element_forces"]) == 3 and v["checks"]["passed"]
    # The local numerical critic is independent of the selected engine.
    assert v["displacements"]["b"][0] > 0


@pytest.mark.parametrize("engine", ["openseespy", "oofem"])
def test_assumed_material_stiffness_sensitivity_is_explicit(tmp_path, engine):
    m = cantilever()
    m["materials"][0]["E_mpa"] *= 0.7
    m["materials"][0]["source"] = (
        "Synthetic 70 percent residual effective stiffness sensitivity; not measured degradation."
    )
    _, _, _, v = run_live(tmp_path, m, engine, "vertical")
    assert v["displacements"]["tip"][1] == pytest.approx(-2.328 / 0.7, rel=1e-7)


def test_mcp_round_trip_solve_and_trust_boundary(tmp_path):
    if os.environ.get("TEE_STRUCTURAL_LIVE") != "1":
        pytest.skip("real-engine MCP gate")
    import anyio
    from mcp.client import Client

    from tee.app import TeeApp
    from tee.kernel import trustctx
    from tee.kernel.adapter import FakeAdapter
    from tee.server import build_server
    from tee.structural.tools import register_structural_tools

    trustctx.install("live-turn", ())
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_structural_tools(app, tmp_path)

    async def work():
        async with Client(build_server(app)) as c:
            assert len((await c.list_tools()).tools) == 17

            async def call(name, args):
                r = await c.call_tool("tee_call", {"name": name, "args": args})
                data = json.loads(next(x.text for x in r.content if x.type == "text"))
                assert data["ok"], data
                return data

            a = await call("st_model", {"model": cantilever()})
            job = await call(
                "st_solve",
                {
                    "model_id": a["model_id"],
                    "expected_revision": 1,
                    "case": "vertical",
                    "engine": "openseespy",
                },
            )
            for _ in range(100):
                r = app.jobs.status(job["job"])
                if r["state"] not in ("queued", "running"):
                    break
                await anyio.sleep(0.02)
            assert r["state"] == "done", r
            result = await call(
                "st_result",
                {
                    "model_id": a["model_id"],
                    "run_id": r["result"]["run_id"],
                    "collection": "displacements",
                },
            )
            assert result["rows"][1]["values"][1] == pytest.approx(-2.328)

    try:
        anyio.run(work)
    finally:
        app.shutdown()
        trustctx.install("content-derived", ())


def test_no_solver_libraries_imported_or_vendored_in_tee():
    import ast

    import tee.structural

    root = Path(tee.structural.__file__).parent
    forbidden = {"openseespy", "openseespymac", "code_aster", "oofempy", "pyvista", "vtk"}
    for p in root.glob("*.py"):
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {n.name.split(".")[0] for n in node.names} & forbidden
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden
    assert not any(p.suffix in (".so", ".dylib", ".dll", ".pyd") for p in root.rglob("*"))


def test_structural_job_respects_enforced_existing_trust_band(tmp_path):
    from tee.app import TeeApp
    from tee.kernel import trustctx
    from tee.kernel.adapter import FakeAdapter
    from tee.structural.tools import register_structural_tools

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_structural_tools(app, tmp_path)
    try:
        trustctx.install("live-turn", ())
        model = app.registry.call("st_model", {"model": cantilever()})
        app.registry.grants.enforce_quality_band = True
        trustctx.install("content-derived", ("untrusted research document",))
        with pytest.raises(TeeError):
            app.registry.call(
                "st_solve",
                {
                    "model_id": model["model_id"],
                    "expected_revision": 1,
                    "case": "vertical",
                    "engine": "openseespy",
                },
            )
        assert not list(app.structural.folder(model["model_id"]).glob("run_*"))
    finally:
        app.shutdown()
        trustctx.install("content-derived", ())


@pytest.mark.parametrize("engine", ["openseespy", "oofem"])
def test_simply_supported_end_nodes_do_not_claim_member_extrema(tmp_path, engine):
    if os.environ.get("TEE_STRUCTURAL_LIVE") != "1":
        pytest.skip("real-engine nodal extrema gate")
    m = cantilever()
    m["supports"] = [
        {"node": "base", "fixed": [True, True, False], "source": "Synthetic pin"},
        {"node": "tip", "fixed": [False, True, False], "source": "Synthetic roller"},
    ]
    service = StructuralService(tmp_path)
    saved = service.save(m)
    result = service.solve(saved["model_id"], 1, "udl", engine, threading.Event())
    assert result["max_nodal_translation_mm"] == pytest.approx(0, abs=1e-12)
    assert result["max_nodal_rotation_rad"] > 0
    assert result["internal_member_extrema"] == "not_evaluated"
    assert "max_translation_mm" not in result
