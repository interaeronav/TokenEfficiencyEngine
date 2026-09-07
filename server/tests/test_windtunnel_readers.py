"""A72 P1: readers never trust a column position or an assumed dialect.

Every parser here keys on the file's own header: the coefficient reader
survives a reordered header and names a missing column, the SU2 history
reader takes its columns from the quoted CSV header, the VSPAERO polar
reader finds its header row wherever the banner ends. The goldens under
tests/data/windtunnel were transcribed from runs TEE made (see the README
there); the fork detector and the Allrun parser decide adoption.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tee.kernel.errors import TeeError
from tee.windtunnel import case as case_mod
from tee.windtunnel import cfdof, engines, foam, paraview, su2, vsp

DATA = Path(__file__).parent / "data" / "windtunnel"

# -- OpenFOAM ------------------------------------------------------------------


def test_coefficient_reader_keys_on_the_header_and_maps_canonical_names():
    data = foam.read_coefficients(DATA / "coefficient_v2606.dat")
    assert data["columns"][:5] == ["Time", "Cd", "Cd(f)", "Cd(r)", "Cl"]
    assert len(data["rows"]) == 5
    last = data["rows"][-1]
    assert last["cd"] == pytest.approx(0.0114069) and last["cl"] == pytest.approx(0.4102003)
    assert last["cm"] == pytest.approx(0.0005286)  # CmPitch -> cm
    assert last["cd_f"] == pytest.approx(0.0056511)
    assert last["Time"] == 5.0


def test_coefficient_reader_survives_a_reordered_header_and_names_a_missing_column(tmp_path):
    reordered = tmp_path / "forceCoeffs.dat"
    reordered.write_text("# Time Cl Cd CmPitch\n10 0.40 0.010 0.001\n11 0.41 0.011 0.002\n")
    rows = foam.read_coefficients(reordered)["rows"]
    assert rows[-1]["cl"] == 0.41 and rows[-1]["cd"] == 0.011 and rows[-1]["cm"] == 0.002
    no_lift = tmp_path / "coefficient.dat"
    no_lift.write_text("# Time Cd CmPitch\n10 0.010 0.001\n")
    row = foam.read_coefficients(no_lift)["rows"][0]
    assert "cd" in row and "cl" not in row
    headless = tmp_path / "x.dat"
    headless.write_text("10 0.010 0.001\n")
    with pytest.raises(ValueError, match="header"):
        foam.read_coefficients(headless)
    ragged = tmp_path / "r.dat"
    ragged.write_text("# Time Cd Cl\n1 0.1\n2 0.1 0.2\n3 x y\n")
    assert len(foam.read_coefficients(ragged)["rows"]) == 1  # short and unparsable rows skipped


def test_coefficient_files_are_found_in_time_order(tmp_path):
    for t in ("0", "500"):
        d = tmp_path / "postProcessing" / "forceCoeffs1" / t
        d.mkdir(parents=True)
        (d / "coefficient.dat").write_text("# Time Cd Cl\n")
    (tmp_path / "postProcessing" / "forceCoeffs1" / "500" / "notes.txt").write_text("x")
    found = foam.find_coefficient_files(tmp_path)
    assert [p.parent.name for p in found] == ["0", "500"]
    assert foam.find_coefficient_files(tmp_path / "nowhere") == []


LOG = """Time = 1

smoothSolver:  Solving for Ux, Initial residual = 0.1, Final residual = 0.01, No Iterations 1
smoothSolver:  Solving for Uy, Initial residual = 0.2, Final residual = 0.02, No Iterations 1
GAMG:  Solving for p, Initial residual = 0.5, Final residual = 0.005, No Iterations 3
GAMG:  Solving for p, Initial residual = 0.3, Final residual = 0.003, No Iterations 3
smoothSolver:  Solving for omega, Initial residual = 0.01, Final residual = 0.001, No Iterations 1
bounding k, min: -1e-3 max: 2 average: 0.1
ExecutionTime = 0.1 s
Time = 2

smoothSolver:  Solving for Ux, Initial residual = 0.05, Final residual = 0.005, No Iterations 1
GAMG:  Solving for p, Initial residual = 0.2, Final residual = 0.002, No Iterations 3
End
"""


def test_log_scraper_takes_the_initial_residual_of_the_first_solve_per_step():
    parsed = foam.parse_log(LOG)
    assert parsed["times"] == [1.0, 2.0]
    assert parsed["residuals"]["Ux"] == [0.1, 0.05]
    assert parsed["residuals"]["p"] == [0.5, 0.2]  # the second p solve in step 1 is ignored
    assert parsed["residuals"]["omega"] == [0.01]
    assert parsed["bounded"] == {"k": 1}
    assert parsed["ended"] is True and parsed["fatal"] is False
    fatal = foam.parse_log(LOG + "--> FOAM FATAL ERROR:\nboom\n")
    assert fatal["fatal"] is True
    lines = foam.last_error_lines(
        "a\nb\n--> FOAM FATAL IO ERROR:\ncannot find file\nFOAM exiting\n"
    )
    assert lines[0].startswith("--> FOAM FATAL") and "cannot find file" in lines[1]
    assert foam.last_error_lines("one\ntwo\nthree\nfour\n", 2) == ["three", "four"]


CHECK_OK = (
    "Mesh stats\n    points:           32400\n    cells:            16000\n"
    "Max non-orthogonality = 12.3 average: 2.1\n    Max skewness = 1.9 OK.\n"
    "    Max aspect ratio = 242.9 OK.\n\nMesh OK.\n\nEnd\n"
)
CHECK_SKEW = (
    "    cells:            16000\n  ***Max skewness = 12.739298, 6 highly skew faces "
    "detected which may impair the quality of the results\n\nFailed 1 mesh checks.\nEnd\n"
)
CHECK_BAD = (
    "    cells:            10\n  ***Boundary openness (0.3 0.1 0.2) possible hole in "
    "boundary description.\n  ***Zero or negative cell volume detected.\n\n"
    "Failed 2 mesh checks.\n"
)


def test_checkmesh_summary_is_read_from_the_report_text():
    ok = foam.parse_checkmesh(CHECK_OK)
    assert ok["ok"] is True and ok["cells"] == 16000 and ok["max_skew"] == 1.9
    assert ok["max_nonortho"] == 12.3 and ok["max_aspect"] == 242.9 and ok["failed"] == []
    skew = foam.parse_checkmesh(CHECK_SKEW)
    assert skew["ok"] is False and skew["failed_checks"] == 1
    assert skew["failed"][0].startswith("Max skewness = 12.739298")
    bad = foam.parse_checkmesh(CHECK_BAD)
    assert bad["failed_checks"] == 2 and len(bad["failed"]) == 2
    nothing = foam.parse_checkmesh("--> FOAM FATAL IO ERROR: cannot find file controlDict\n")
    assert nothing["ok"] is False and "cells" not in nothing


@pytest.mark.parametrize(
    ("version", "fork"),
    [
        ("v2606", "com"),
        ("v1912", "com"),
        ("v2312.1", "com"),
        ("12", "org"),
        ("9", "org"),
        ("dev", "org"),
        ("unknown", "unknown"),
        ("", "unknown"),
    ],
)
def test_fork_detection(version, fork):
    assert foam.fork_of(version)[0] == fork
    assert foam.SUPPORTED_DIALECTS == ("com",)


def test_allrun_parser_returns_argv_of_the_binaries_never_the_script():
    text = """#!/bin/sh
cd "${0%/*}" || exit
. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions
runApplication blockMesh
runApplication surfaceFeatureExtract
runApplication snappyHexMesh -overwrite
runApplication decomposePar -force > log.decomposePar 2>&1
runParallel $(getApplication)
runApplication -s final simpleFoam
runApplication foamToVTK | tee log
"""
    assert foam.solver_sequence(text) == [
        ["blockMesh"],
        ["surfaceFeatureExtract"],
        ["snappyHexMesh", "-overwrite"],
        ["decomposePar", "-force"],
        ["(getApplication)"],
        ["simpleFoam"],
        ["foamToVTK"],
    ]
    assert (
        foam.controldict_application("application     simpleFoam;\nstartFrom startTime;")
        == "simpleFoam"
    )
    assert foam.controldict_application("no application here") is None
    assert list(foam.default_sequence(True)) == [
        ["blockMesh"],
        ["surfaceFeatureExtract"],
        ["snappyHexMesh", "-overwrite"],
        ["checkMesh"],
    ]
    assert list(foam.default_sequence(False)) == [["blockMesh"], ["checkMesh"]]


def test_field_bcs_and_patch_names_from_written_files(tmp_path):
    s = foam.FoamSetup(
        U_inf=(10.0, 0.0, 0.0),
        nu=1e-5,
        inlet_patches=("inlet",),
        outlet_patches=("outlet",),
        freestream_patches=(),
        wall_patches=("body",),
        empty_patches=(),
    )
    bcs = foam.field_bcs(foam.fields_0(s)["U"])
    assert bcs == {"inlet": "fixedValue", "outlet": "inletOutlet", "body": "noSlip"}
    boundary = """FoamFile
{
    version     2.0;
    format      ascii;
    class       polyBoundaryMesh;
    object      boundary;
}
3
(
    airfoil
    {
        type            wall;
        inGroups        List<word> 1(wall);
        nFaces          200;
        startFace       31600;
    }
    farfield
    {
        type            patch;
        nFaces          200;
        startFace       31800;
    }
    frontAndBack
    {
        type            empty;
        nFaces          32000;
        startFace       32000;
    }
)
"""
    assert foam.patch_names(boundary) == [
        ("airfoil", "wall"),
        ("farfield", "patch"),
        ("frontAndBack", "empty"),
    ]


# -- SU2 ---------------------------------------------------------------------------


def test_history_reader_takes_columns_from_the_quoted_header():
    data = su2.read_history(DATA / "history_su2_840.csv")
    assert data["columns"][:4] == ["Time_Iter", "Outer_Iter", "Inner_Iter", "Time(sec)"]
    last = data["rows"][-1]
    assert last["cl"] == pytest.approx(0.024969) and last["cd"] == pytest.approx(0.029103)
    assert last["cm"] == pytest.approx(0.002498)  # CMz for a 2-D case
    assert last["rms[Rho]"] == pytest.approx(-2.3474)


def test_history_reader_survives_reordered_columns_and_skips_short_rows(tmp_path):
    p = tmp_path / "history.csv"
    p.write_text('"Inner_Iter" , "CL" , "CD" , "rms[Rho]"\n0,0.1,0.02,-2\n1,0.2\n2,0.3,0.03,-3\n')
    rows = su2.read_history(p)["rows"]
    assert [r["cl"] for r in rows] == [0.1, 0.3] and rows[-1]["cd"] == 0.03
    empty = tmp_path / "e.csv"
    empty.write_text("")
    with pytest.raises(ValueError):
        su2.read_history(empty)


_RULE = "+" + "-" * 71 + "+"
_TAIL = "|          CL|          CD|"
SCREEN = "\n".join(
    [
        _RULE,
        "|  Inner_Iter|   Time(sec)|    rms[Rho]|   rms[RhoU]|   rms[RhoV]|   rms[RhoE]" + _TAIL,
        _RULE,
        "|           0|  5.1200e-02|   -2.045069|   -2.338395|   -2.561989|   -1.835130"
        "|    0.002215|    0.031120|",
        "|           1|  1.0430e-01|   -2.120745|   -2.411057|   -2.636699|   -1.910657"
        "|    0.008021|    0.030612|",
        "|   not a row|",
        "All convergence criteria satisfied.",
        "",
    ]
)


def test_screen_log_parser_reads_the_pipe_table_and_the_exit_banner():
    scr = su2.parse_screen_log(SCREEN)
    assert scr["columns"][0] == "Inner_Iter" and scr["columns"][-1] == "CD"
    assert len(scr["rows"]) == 2 and scr["rows"][-1]["cl"] == pytest.approx(0.008021)
    assert scr["converged"] is True and scr["max_iter"] is False and scr["error"] is None
    err = su2.parse_screen_log('Error in "CSolver":\n-----\nError Exit: NaN\n')
    assert err["error"] and "NaN" in err["error"]
    assert su2.parse_screen_log("Maximum number of iterations reached (ITER = 5)")["max_iter"]


def test_surface_csv_reader_with_a_limit(tmp_path):
    p = tmp_path / "surface_flow.csv"
    p.write_text(
        '"PointID","x","y","Pressure"\n0,0.0,0.0,101325\n1,0.5,0.1,90000\n2,1.0,0.0,101000\n'
    )
    data = su2.read_surface_csv(p, limit=2)
    assert data["columns"] == ["PointID", "x", "y", "Pressure"] and len(data["rows"]) == 2


# -- OpenVSP -----------------------------------------------------------------------


def test_polar_reader_finds_the_header_row_after_the_banner():
    data = vsp.read_polar(DATA / "wing_ar10.polar")
    assert data["columns"][:3] == ["Beta", "Mach", "AoA"]
    rows = data["rows"]
    assert [r["alpha"] for r in rows] == [0.0, 2.0, 4.0, 6.0]
    assert rows[-1]["cl"] == pytest.approx(0.51363) and rows[-1]["cdi"] == pytest.approx(0.010481)
    assert rows[-1]["e"] == pytest.approx(0.9545) and rows[-1]["l_over_d"] == pytest.approx(32.8017)


def test_polar_reader_refuses_a_file_without_the_header(tmp_path):
    p = tmp_path / "x.polar"
    p.write_text("1 2 3\n4 5 6\n")
    with pytest.raises(ValueError, match="header"):
        vsp.read_polar(p)


def test_lod_reader_returns_the_last_block(tmp_path):
    p = tmp_path / "w.lod"
    p.write_text(
        "Wing S Yavg Chord V/Vinf Cl Cd Cs\n1 1.2 -4.4 1.0 1.0 0.10 0.005 0\n"
        "1 1.2 -3.1 1.0 1.0 0.12 0.005 0\n"
        "Wing S Yavg Chord V/Vinf Cl Cd Cs\n1 1.2 -4.4 1.0 1.0 0.30 0.009 0\n"
    )
    lod = vsp.read_lod(p)
    assert lod["blocks"] == 2 and lod["last"]["rows"][0]["Cl"] == 0.30


def test_script_facts_and_model_detection(tmp_path):
    assert vsp.script_facts("TotalSpan=10\nTotalArea= 9.5\nDONE") == {
        "TotalSpan": 10.0,
        "TotalArea": 9.5,
    }
    good = tmp_path / "m.vsp3"
    good.write_text('<?xml version="1.0"?>\n<Vsp_Geometry>\n</Vsp_Geometry>\n')
    assert vsp.vsp3_is_model(good) is True
    other = tmp_path / "o.vsp3"
    other.write_text("<html/>")
    assert vsp.vsp3_is_model(other) is False and vsp.vsp3_is_model(tmp_path / "none.vsp3") is False


# -- ParaView ------------------------------------------------------------------------


def test_csv_columns_sampling_and_stats(tmp_path):
    p = tmp_path / "line.csv"
    lines = ['"U:0","U:1","U:2","p","vtkValidPointMask","arc_length"']
    for k in range(200):
        lines.append(f"{3.0 * k},{4.0 * k},0,{-k},1,{k * 0.01}")
    lines.append("x,y,z,,1,2.0")  # a row that will not parse -> NaN, never a crash
    p.write_text("\n".join(lines) + "\n")
    cols = paraview.read_csv_columns(p)
    assert len(cols["U:0"]) == 201 and cols["U:0"][-1] != cols["U:0"][-1]  # NaN
    sample = paraview.csv_sample(cols, "U", limit=64)
    assert sample["n_total"] == 201 and sample["n"] <= 64
    assert sample["U_mag"][1] == pytest.approx(5.0 * (sample["s"][1] / 0.01))  # 3-4-5
    assert sample["stats"]["n"] == 200
    scalar = paraview.csv_sample(cols, "p", limit=10)
    assert scalar["n"] == 10 and "p" in scalar and "p_mag" not in scalar
    with pytest.raises(TeeError) as err:
        paraview.csv_sample(cols, "omega")
    assert err.value.code == "wt_field_missing"
    st = paraview.stats([5.0, 1.0, 3.0, float("nan"), 4.0, 2.0])
    assert st["n"] == 5 and st["min"] == 1.0 and st["max"] == 5.0 and st["mean"] == 3.0
    assert paraview.stats([float("nan")]) == {"n": 0}


# -- the digest law -----------------------------------------------------------------


def test_digest_thins_long_arrays_and_truncates_long_strings():
    payload = {
        "rows": list(range(1000)),
        "text": "x" * 5000,
        "nested": {"ok": [1, 2, 3], "deep": [[0] * 100]},
    }
    out = case_mod.digest(payload)
    rows = out["rows"]  # a thinned array says so and keeps its first element
    assert rows["thinned"] is True and rows["n_total"] == 1000 and rows["every"] == 16
    assert len(rows["items"]) <= case_mod.MAX_ARRAY and rows["items"][0] == 0
    assert len(out["text"]) <= case_mod.MAX_STRING and out["text"].endswith("[5000 chars]")
    assert out["nested"]["ok"] == [1, 2, 3]
    assert len(out["nested"]["deep"][0]["items"]) <= case_mod.MAX_ARRAY
    assert case_mod.digest({"v": float("nan"), "w": float("inf")}) == {"v": None, "w": None}
    assert (case_mod.MAX_ARRAY, case_mod.MAX_STRING) == (64, 2048)


# -- adoption -----------------------------------------------------------------------


def _write_case(tmp_path: Path) -> Path:
    from tee.windtunnel import airfoil, mesh2d

    case = tmp_path / "case"
    foam.write_case(case, foam.FoamSetup(U_inf=(30.0, 0.0, 0.0), nu=1.5e-5))
    mesh2d.write_polymesh(
        case, mesh2d.omesh(airfoil.naca4("0012", 20), first_cell=1e-3, nj=6, radius_c=10.0)
    )
    (case / "Allrun").write_text(
        "#!/bin/sh\n# CfdOF generated\nrunApplication blockMesh\nrunApplication simpleFoam\n"
        "runApplication foamToVTK\n"
    )
    (case / "processor0").mkdir()
    (case / "processor0" / "junk").write_text("x" * 100)
    return case


def test_detect_recognises_the_three_case_shapes_and_refuses_the_rest(tmp_path):
    case = _write_case(tmp_path)
    assert cfdof.detect(case) == "openfoam"
    cfg = tmp_path / "inv.cfg"
    cfg.write_text("SOLVER= EULER\nMESH_FILENAME= mesh.su2\n")
    assert cfdof.detect(cfg) == "su2"
    model = tmp_path / "m.vsp3"
    model.write_text("<Vsp_Geometry></Vsp_Geometry>")
    assert cfdof.detect(model) == "vsp3"
    with pytest.raises(TeeError) as err:
        cfdof.detect(tmp_path)
    assert err.value.code == "wt_not_a_case"


def test_summary_and_copy_of_a_written_case(tmp_path):
    case = _write_case(tmp_path)
    s = cfdof.summarise_openfoam(case)
    assert s["solver"] == "simpleFoam" and s["has_forceCoeffs"] is True
    assert s["turbulence"] == "kOmegaSST" and s["dialect"] == "com" and s["has_mesh"] is True
    assert ("airfoil", "wall") in s["patches"] and s["inlet_U"] == [30.0, 0.0, 0.0]
    assert s["U_bcs"]["airfoil"] == "noSlip"
    assert s["sequence"] == [["blockMesh"], ["simpleFoam"]] and s["unknown_in_scripts"] == [
        "foamToVTK"
    ]
    assert s["cfdof"] is True
    dst = tmp_path / "copy"
    copied = cfdof.copy_case(case, dst)
    assert copied["bytes"] > 0 and not (dst / "processor0").exists()
    assert (dst / "system" / "controlDict").is_file()
    momentum = tmp_path / "org"
    (momentum / "system").mkdir(parents=True)
    (momentum / "constant").mkdir()
    (momentum / "system" / "controlDict").write_text("application foamRun;\n")
    (momentum / "constant" / "momentumTransport").write_text(
        "simulationType RAS;\nRAS { model kEpsilon; }\n"
    )
    assert cfdof.summarise_openfoam(momentum)["dialect"] == "org"
    assert cfdof.summarise_openfoam(momentum)["turbulence"] == "kEpsilon"


# -- engine discovery ----------------------------------------------------------------


def test_binary_discovery_refuses_a_wrong_explicit_path_and_names_the_install(
    tmp_path, monkeypatch
):
    with pytest.raises(TeeError) as err:
        engines.find_su2({"su2": str(tmp_path / "nowhere")}, probe_version=False)
    assert err.value.code == "wt_bad_config"
    monkeypatch.setattr(engines.shutil, "which", lambda name: None)
    monkeypatch.setattr(engines.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.delenv("SU2_RUN", raising=False)
    with pytest.raises(TeeError) as err:
        engines.find_su2({}, probe_version=False)
    assert err.value.code == "wt_su2_missing" and "SU2-v8.4.0" in err.value.fix
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "SU2_CFD").write_text("#!/bin/sh\n")
    found = engines.find_su2({"su2": str(bindir)}, probe_version=False)
    assert found.path == str(bindir / "SU2_CFD") and found.via == "config"
    with pytest.raises(TeeError) as err:
        engines.find_openfoam({"openfoam": str(tmp_path / "not-foam")}, probe_version=False)
    assert err.value.code == "wt_bad_config"
    (bindir / "simpleFoam").write_text("#!/bin/sh\n")
    route = engines.find_openfoam({"openfoam": str(bindir)}, probe_version=False)
    assert route.kind == "bindir" and route.argv("checkMesh", "-case", "x") == [
        str(bindir / "checkMesh"),
        "-case",
        "x",
    ]
    bashrc = tmp_path / "of" / "etc" / "bashrc"
    bashrc.parent.mkdir(parents=True)
    bashrc.write_text("# fake bashrc\n")
    route = engines.find_openfoam({"openfoam": str(tmp_path / "of")}, probe_version=False)
    assert route.kind == "bashrc" and route.argv("simpleFoam", "-case", "c")[:2] == ["bash", "-c"]
    assert "mpirun -np 4 simpleFoam -parallel" in " ".join(
        route.parallel_argv("simpleFoam", 4, "-case", "c")
    )
    entry = engines.FoamInstall(
        "entry", "/Applications/OpenFOAM-v2606.app/Contents/Resources/etc/openfoam"
    )
    assert entry.argv("simpleFoam", "-case", "c")[0].endswith("etc/openfoam")


def test_install_lines_carry_a_size_or_a_date_per_platform():
    for engine, per_platform in engines.INSTALL.items():
        for system in ("Darwin", "Linux"):
            line = per_platform[system]
            assert "2026" in line or "download" in line, (engine, system)


def test_pvpython_never_writes_bytecode_into_the_app_bundle(tmp_path, monkeypatch):
    """A signed .app is sealed: adding files to it breaks the signature and
    macOS then refuses to launch the application. pvpython imports its own
    modules from inside the bundle, so without PYTHONDONTWRITEBYTECODE it
    writes ~200 .pyc files there on a first run and bricks ParaView -
    measured 2026-09-07 on the owner's Mac, which is how the bug was found.
    """
    import subprocess as sp

    from tee.windtunnel import paraview as pv

    seen = {}

    def fake_run(argv, **kw):
        seen.update(kw.get("env") or {})
        return sp.CompletedProcess(argv, 0, stdout="OK\n", stderr="")

    monkeypatch.setattr(pv.subprocess, "run", fake_run)
    pv.run_script("/nonexistent/pvpython", "print('OK')", tmp_path, render=False)
    assert seen.get("PYTHONDONTWRITEBYTECODE") == "1", (
        "pvpython must not cache bytecode into the signed ParaView bundle"
    )
