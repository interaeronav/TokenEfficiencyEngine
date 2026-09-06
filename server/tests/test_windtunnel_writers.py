"""A68 P1: what TEE writes for the engines - byte-stable dictionaries in the
openfoam.com dialect, an SU2 .cfg with the verified QuickStart keys, the two
AngelScripts, the pvpython scripts - and the one defect the first real run
found (a 16-character key glued to its value)."""

from __future__ import annotations

import re

import pytest

from tee.windtunnel import foam, paraview, report, su2, vsp


def has(text: str, key: str, value: str) -> bool:
    """`key<spaces>value;` on a line of its own, whatever the padding."""
    return re.search(rf"^\s*{re.escape(key)}\s+{re.escape(value)};", text, re.M) is not None


def _setup(**kw) -> foam.FoamSetup:
    base = {"U_inf": (30.0, 2.1, 0.0), "nu": 1.46e-5}
    base.update(kw)
    return foam.FoamSetup(**base)


# -- the serialiser -----------------------------------------------------------


def test_foam_file_is_byte_stable_and_never_glues_a_long_key_to_its_value():
    """`writeCompression` is exactly 16 characters: the first serialiser
    padded keys to 16 and wrote `writeCompressionoff;`, which simpleFoam
    refused. A key is always followed by at least one space."""
    text = foam.control_dict(_setup())
    assert text == foam.control_dict(_setup())
    assert "writeCompression off;" in text
    assert "runTimeModifiable true;" in text
    assert "writeCompressionoff" not in text
    assert text.startswith("/*") and "generated-by: tee.windtunnel.foam" in text


def test_control_dict_carries_the_force_coefficient_setup_in_wind_axes():
    s = _setup(Aref=0.1, lRef=1.0, liftDir=(-0.0698, 0.9976, 0.0), dragDir=(0.9976, 0.0698, 0.0))
    text = foam.control_dict(s)
    assert has(text, "application", "simpleFoam")
    assert has(text, "libs", '("libforces.so")')
    assert has(text, "type", "forceCoeffs")
    assert has(text, "patches", "(airfoil)")
    assert has(text, "liftDir", "(-0.0698 0.9976 0)")
    assert has(text, "Aref", "0.1")
    assert "magUInf" in text
    bare = foam.control_dict(s, functions=False)
    assert "forceCoeffs" not in bare and "functions" not in bare


def test_fv_solution_and_schemes_follow_the_turbulence_choice():
    turb = foam.fv_solution(_setup())
    assert "residualControl" in turb and '"(k|omega)"' in turb and "1e-05" in turb
    assert "$p;" in turb and "grad(U);" in turb  # bare entries, not `$p ;`
    assert has(turb, "consistent", "yes")
    lam = foam.fv_solution(_setup(turbulence="laminar"))
    assert "omega" not in lam
    assert "div(phi,k)" in foam.fv_schemes(_setup())
    assert "div(phi,k)" not in foam.fv_schemes(_setup(turbulence="laminar"))
    assert "kOmegaSST" in foam.turbulence_properties(_setup())
    assert "laminar" in foam.turbulence_properties(_setup(turbulence="laminar"))
    assert has(foam.transport_properties(_setup()), "nu", "1.46e-05")
    assert has(foam.decompose_par_dict(4), "numberOfSubdomains", "4")


def test_freestream_turbulence_follows_intensity_and_viscosity_ratio():
    s = _setup(U_inf=(10.0, 0.0, 0.0), turbulence_intensity=0.05, viscosity_ratio=10.0, nu=1e-5)
    assert s.magU == pytest.approx(10.0)
    assert s.k_inf == pytest.approx(1.5 * (0.05 * 10.0) ** 2)
    assert s.omega_inf == pytest.approx(s.k_inf / (10.0 * 1e-5))


def test_initial_fields_give_every_patch_role_its_condition():
    s = _setup(
        wall_patches=("body", "ground"),
        freestream_patches=(),
        inlet_patches=("inlet",),
        outlet_patches=("outlet",),
        slip_patches=("sides", "top"),
        empty_patches=(),
        wall_treatment="wall_function",
    )
    fields = foam.fields_0(s)
    assert set(fields) == {"U", "p", "k", "omega", "nut"}
    U = fields["U"]
    assert "uniform (30 2.1 0)" in U
    for patch, bc in (
        ("inlet", "fixedValue"),
        ("outlet", "inletOutlet"),
        ("sides", "slip"),
        ("body", "noSlip"),
    ):
        assert bc in U.split(patch, 1)[1].split("}")[0], (patch, bc)
    assert "nutkWallFunction" in fields["nut"] and "kqRWallFunction" in fields["k"]
    low = foam.fields_0(_setup())  # the 2-D defaults: airfoil / farfield / frontAndBack, low-Re
    assert "freestreamVelocity" in low["U"] and "freestreamPressure" in low["p"]
    assert "empty" in low["U"].split("frontAndBack", 1)[1].split("}")[0]
    assert "nutLowReWallFunction" in low["nut"] and "uniform 1e-10" in low["k"]
    assert set(foam.fields_0(_setup(turbulence="laminar"))) == {"U", "p"}


def test_write_case_and_the_mesh_stub_leave_the_expected_files(tmp_path):
    written = foam.write_case(tmp_path / "case", _setup(cores=2))
    assert "system/controlDict" in written and "system/decomposeParDict" in written
    assert "0/U" in written and "0/omega" in written and "constant/transportProperties" in written
    again = tmp_path / "again"
    foam.write_case(again, _setup(cores=2))
    for rel in written:  # byte-stable across two writes: the dictionary hash is meaningful
        assert (tmp_path / "case" / rel).read_bytes() == (again / rel).read_bytes()
    mesh_dir = tmp_path / "mesh"
    stub = foam.write_mesh_system(mesh_dir)
    assert stub == ["system/controlDict", "system/fvSchemes", "system/fvSolution"]
    assert "functions" not in (mesh_dir / "system/controlDict").read_text()
    assert foam.write_mesh_system(mesh_dir) == []  # never overwrites a case's own


def test_block_mesh_and_snappy_dictionaries_name_the_tunnel_patches():
    t = foam.Tunnel3D(
        xmin=-5,
        xmax=16,
        ymin=-5,
        ymax=5,
        zmin=-5,
        zmax=5,
        base_cell=0.25,
        body_name="body",
        body_bbox=((0, -0.5, -0.5), (1, 0.5, 0.5)),
        surface_levels=(3, 4),
        layers=5,
    )
    bm = foam.block_mesh_dict(t)
    assert "hex (0 1 2 3 4 5 6 7) (84 40 40)" in bm
    for name in ("inlet", "outlet", "sides", "top", "ground"):
        assert name in bm
    assert not has(bm, "type", "wall")
    grounded = foam.block_mesh_dict(foam.Tunnel3D(**{**t.__dict__, "ground": True}))
    assert "wall" in grounded.split("ground", 1)[1]
    sn = foam.snappy_dict(t)
    assert "body" in sn and "(3 4)" in sn and "nSurfaceLayers" in sn and "locationInMesh" in sn
    assert "body.stl" in foam.surface_feature_extract_dict("body")
    assert "includedAngle" in foam.surface_feature_extract_dict("body")
    assert '#includeEtc "caseDicts/meshQualityDict"' in foam.mesh_quality_dict()


# -- SU2 ----------------------------------------------------------------------


def test_su2_cfg_writes_the_verified_keys_for_euler_and_rans(tmp_path):
    euler = su2.Su2Setup(mesh_file="/m/mesh.su2", solver="EULER", mach=0.8, aoa_deg=1.25)
    lines = su2.write_cfg(tmp_path / "e.cfg", euler)
    text = "\n".join(lines)
    assert lines[0] == "% generated-by: tee.windtunnel.su2"
    for key in (
        "SOLVER= EULER",
        "MACH_NUMBER= 0.8",
        "AOA= 1.25",
        "MARKER_EULER= ( airfoil )",
        "MARKER_FAR= ( farfield )",
        "MESH_FILENAME= /m/mesh.su2",
        "TABULAR_FORMAT= CSV",
        "CONV_FILENAME= history",
        "HISTORY_OUTPUT= (ITER, WALL_TIME, RMS_RES, AERO_COEFF)",
        "OUTPUT_FILES= (RESTART, PARAVIEW, SURFACE_CSV)",
    ):
        assert key in text, key
    assert "REYNOLDS_NUMBER" not in text and "KIND_TURB_MODEL" not in text
    rans = su2.Su2Setup(mesh_file="/m/mesh.su2", solver="RANS", reynolds=2.05e6, turbulence="SST")
    text = "\n".join(su2.write_cfg(tmp_path / "r.cfg", rans))
    assert "KIND_TURB_MODEL= SST" in text and "SST_OPTIONS= V2003m" in text
    assert "REYNOLDS_NUMBER= 2.05e+06" in text and "MARKER_HEATFLUX= ( airfoil, 0.0 )" in text
    back = su2.read_cfg(tmp_path / "r.cfg")
    assert back["SOLVER"] == "RANS" and back["MESH_FILENAME"] == "/m/mesh.su2"


# -- OpenVSP ------------------------------------------------------------------


def test_wing_spec_geometry():
    w = vsp.WingSpec(span=10.0, root_chord=1.0)
    assert (w.area, w.aspect_ratio, w.mac) == (10.0, 10.0, 1.0)
    tapered = vsp.WingSpec(span=8.0, root_chord=1.0, tip_chord=0.5)
    assert tapered.area == pytest.approx(6.0)
    assert tapered.mac == pytest.approx((2 / 3) * (1 + 0.5 + 0.25) / 1.5)


def test_wing_script_uses_the_harvested_api_names():
    text = vsp.wing_script("wing", vsp.WingSpec(span=10.0, root_chord=1.0, airfoil="0012"))
    assert text.startswith("// generated-by: tee.windtunnel.vsp")
    for call in (
        'AddGeom( "WING", "" )',
        '"Span", "XSec_1", 5',
        '"Root_Chord", "XSec_1", 1',
        '"ThickChord", "XSecCurve_0", 0.12',
        'WriteVSPFile( "wing.vsp3", SET_ALL )',
        'ExportFile( "wing.stl", SET_ALL, EXPORT_STL )',
        "ComputeDegenGeom( SET_ALL, DEGEN_GEOM_CSV_TYPE )",
        'Print( "DONE" )',
    ):
        assert call in text, call
    assert "CamberLoc" not in text
    assert "CamberLoc" in vsp.wing_script(
        "w", vsp.WingSpec(span=1.0, root_chord=0.2, airfoil="2412")
    )
    with pytest.raises(ValueError):
        vsp.wing_script("w", vsp.WingSpec(span=1.0, root_chord=0.2, airfoil="00x2"))


def test_sweep_script_sets_the_two_measured_vlm_facts_and_refuses_uneven_alphas():
    text = vsp.sweep_script(
        "model.vsp3", alphas=[0.0, 2.0, 4.0, 6.0], mach=0.1, re_cref=2.3e6, ncpu=4
    )
    for call in (
        '"GeomSet", none_set',
        '"ThinGeomSet", all_set',
        '"RefFlag", rf',
        '"WingID", wids',
        "a0.push_back( 0 )",
        "a1.push_back( 6 )",
        "an_pts.push_back( 4 )",
        "m0.push_back( 0.1 )",
        "re.push_back( 2300000 )",
        "ncpu.push_back( 4 )",
        'Print( "POLAR=model.polar" )',
    ):
        assert call in text, call
    assert "ReCref" not in vsp.sweep_script("m.vsp3", alphas=[2.0], mach=0.2)
    with pytest.raises(ValueError):
        vsp.sweep_script("m.vsp3", alphas=[0.0, 1.0, 5.0], mach=0.1)
    with pytest.raises(ValueError):
        vsp.sweep_script("m.vsp3", alphas=[], mach=0.1)


# -- ParaView -------------------------------------------------------------------


def test_pvpython_scripts_read_foam_or_vtu_and_never_render_for_a_probe(tmp_path):
    foam_stub = tmp_path / "case.foam"
    line = paraview.line_script(foam_stub, (0, 0, 0), (1, 0, 0), 16, tmp_path / "l.csv")
    assert "OpenFOAMReader" in line and "PlotOverLine" in line and "pol.Resolution = 15" in line
    assert "Render" not in line and "SaveScreenshot" not in line
    vtu = paraview.slice_stats_script(
        tmp_path / "flow.vtu", (0.5, 0, 0), (0, 0, 1), "p", tmp_path / "s.csv"
    )
    assert "XMLUnstructuredGridReader" in vtu and "PointDataArrays=['p']" in vtu
    render = paraview.render_script(foam_stub, "velocity", tmp_path / "v.png", size=(640, 480))
    assert (
        "SaveScreenshot" in render
        and "rv.ViewSize = [640, 480]" in render
        and "('CELLS', 'U')" in render
    )
    assert "Surface With Edges" in paraview.render_script(foam_stub, "mesh", tmp_path / "m.png")
    with pytest.raises(Exception, match=r"wt_bad_view|view preset"):
        paraview.render_script(foam_stub, "vorticity", tmp_path / "x.png")
    with pytest.raises(Exception, match="neither"):
        paraview.line_script(tmp_path / "case.dat", (0, 0, 0), (1, 0, 0), 8, tmp_path / "x.csv")
    stub = paraview.foam_stub(tmp_path)
    assert stub.name == "case.foam" and stub.stat().st_size == 0
    assert paraview.foam_stub(tmp_path) == stub


def test_argv_picks_xvfb_only_for_a_render_with_no_display(tmp_path, monkeypatch):
    script = tmp_path / "s.py"
    monkeypatch.setattr(paraview.platform, "system", lambda: "Linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr(paraview.shutil, "which", lambda name: "/usr/bin/xvfb-run")
    assert paraview.argv_for("/opt/pv", script, render=True)[:3] == [
        "/usr/bin/xvfb-run",
        "-a",
        "/opt/pv",
    ]
    assert paraview.argv_for("/opt/pv", script, render=False) == ["/opt/pv", str(script)]
    monkeypatch.setattr(paraview.shutil, "which", lambda name: None)
    assert paraview.argv_for("/opt/pv", script, render=True) == [
        "/opt/pv",
        "--force-offscreen-rendering",
        str(script),
    ]
    monkeypatch.setenv("DISPLAY", ":0")
    assert paraview.argv_for("/opt/pv", script, render=True) == [
        "/opt/pv",
        "--force-offscreen-rendering",
        str(script),
    ]
    monkeypatch.setattr(paraview.platform, "system", lambda: "Darwin")
    monkeypatch.delenv("DISPLAY", raising=False)
    assert paraview.argv_for("/opt/pv", script, render=True)[1] == "--force-offscreen-rendering"


# -- exports --------------------------------------------------------------------

CASE = {
    "case_id": "wt_test000001",
    "kind": "airfoil2d",
    "engine": "openfoam",
    "engine_dir": "",
    "fidelity": {"chosen": "rans", "reason": "test"},
    "conditions": {
        "V": 30.0,
        "mach": 0.088,
        "Re": 2.05e6,
        "aoa_deg": 4.0,
        "regime": "incompressible",
    },
    "refs": {"Sref": 1.0, "cref": 1.0, "bref": 1.0},
    "geometry": {"kind": "airfoil2d", "name": "NACA 0012"},
    "mesh": {"cells": 16000, "mesh_hash": "abc123"},
}
RUN = {
    "run_id": "run_001",
    "state": "done",
    "engine_version": "v2606",
    "wall_s": 17.2,
    "aoa_deg": 4.0,
    "result": {
        "cl": 0.4356,
        "cd": 0.01091,
        "cm": 0.0006,
        "l_over_d": 39.9,
        "verdict": {"state": "converged", "residual_drop_orders": 5.0},
        "uncertainty": {"trust": "comparative", "label": "deltas only", "cite": "DPW"},
    },
}


def test_exports_write_json_csv_markdown_foam_and_pipeline(tmp_path):
    case = {**CASE, "engine_dir": str(tmp_path / "engine")}
    (tmp_path / "engine").mkdir()
    out = {
        fmt: report.export(None, fmt, case, RUN, tmp_path / "exports")
        for fmt in ("json", "csv", "md", "foam", "pipeline")
    }
    assert out["json"]["bytes"] > 100 and out["json"]["path"].endswith("wt_test000001_run_001.json")
    csv_text = (tmp_path / "exports" / "wt_test000001_run_001.csv").read_text().splitlines()
    assert csv_text[0] == "aoa_deg,mach,cl,cd,cm,l_over_d,state"
    assert csv_text[1].startswith(",,0.4356,0.01091")
    md = (tmp_path / "exports" / "wt_test000001_run_001.md").read_text()
    assert "converged" in md and "comparative" in md and "v2606" in md and "abc123" in md
    assert out["foam"]["path"].endswith("engine/case.foam") and out["foam"]["bytes"] == 0
    toml_text = (tmp_path / "exports" / "wt_test000001_run_001.pipeline.toml").read_text()
    assert "wall_s" in toml_text and "wt_test000001" in toml_text
    with pytest.raises(Exception, match=r"wt_bad_format|export format"):
        report.export(None, "xlsx", case, RUN, tmp_path)
    with pytest.raises(Exception, match=r"wt_no_results|Nothing"):
        report.export(None, "csv", case, {"run_id": "run_002"}, tmp_path)
