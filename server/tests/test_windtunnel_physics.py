"""A68 P1: the physics TEE owns, pinned to the sources its docstrings cite.

Atmosphere rows are the U.S. Standard Atmosphere 1976 / ISO 2533 tables
(sea level, 5 km, the 11 km tropopause, 20 km); the wall-spacing check is
Schlichting's flat-plate correlation; the lifting-line numbers are
Anderson §5.3; NACA 0012's maximum thickness sits at 30 % chord and 2412's
camber at 40 % (Abbott & von Doenhoff §6.4). The O-mesh is judged by the
one property that matters to a solver: no inverted cell anywhere.
"""

from __future__ import annotations

import math
import struct

import pytest

from tee.windtunnel import airfoil, atmosphere, fidelity, mesh2d, physics, su2, verdict

# alt_m, T_K, p_Pa, rho (US76 table, ISO 2533)
ISA_ROWS = [
    (0.0, 288.15, 101325.0, 1.2250),
    (5000.0, 255.65, 54019.9, 0.73612),
    (11000.0, 216.65, 22632.1, 0.36392),
    (20000.0, 216.65, 5474.89, 0.088035),
]


# -- atmosphere ---------------------------------------------------------------


@pytest.mark.parametrize(("alt", "T", "p", "rho"), ISA_ROWS)
def test_isa_rows_to_four_significant_figures(alt, T, p, rho):
    air = atmosphere.isa(alt)
    assert pytest.approx(T, rel=5e-4) == air.T_K
    assert air.p_Pa == pytest.approx(p, rel=5e-4)
    assert air.rho == pytest.approx(rho, rel=5e-4)


def test_sea_level_sound_speed_and_viscosity():
    air = atmosphere.isa(0.0)
    assert air.a == pytest.approx(340.29, rel=1e-4)
    assert air.mu == pytest.approx(1.7894e-5, rel=1e-3)  # Sutherland at 288.15 K


def test_a_hot_day_shifts_temperature_and_density_but_not_pressure():
    std, hot = atmosphere.isa(0.0), atmosphere.isa(0.0, dT_K=15.0)
    assert pytest.approx(std.T_K + 15.0) == hot.T_K
    assert hot.p_Pa == pytest.approx(std.p_Pa)
    assert hot.rho < std.rho


def test_isa_refuses_outside_the_two_layers_it_knows():
    with pytest.raises(ValueError):
        atmosphere.isa(25_000.0)
    with pytest.raises(ValueError):
        atmosphere.isa(-10.0)


def test_conditions_from_speed_and_from_mach_agree():
    a = atmosphere.conditions(L_m=1.0, V_mps=68.058)
    b = atmosphere.conditions(L_m=1.0, mach=0.2)
    assert a["mach"] == pytest.approx(0.2, rel=1e-3)
    assert b["V"] == pytest.approx(68.058, rel=1e-3)
    assert a["Re"] == pytest.approx(b["Re"], rel=1e-3)
    assert a["Re"] == pytest.approx(1.2250 * 68.058 / 1.7894e-5, rel=2e-3)
    assert a["q_Pa"] == pytest.approx(0.5 * 1.2250 * 68.058**2, rel=1e-3)
    assert a["regime"] == "incompressible"


def test_conditions_refuse_both_or_neither_speed():
    with pytest.raises(ValueError):
        atmosphere.conditions(L_m=1.0)
    with pytest.raises(ValueError):
        atmosphere.conditions(L_m=1.0, V_mps=10.0, mach=0.1)
    with pytest.raises(ValueError):
        atmosphere.conditions(L_m=0.0, V_mps=10.0)


@pytest.mark.parametrize(
    ("mach", "word"),
    [
        (0.1, "incompressible"),
        (0.29, "incompressible"),
        (0.5, "subsonic"),
        (0.85, "transonic"),
        (1.19, "transonic"),
        (2.0, "supersonic"),
    ],
)
def test_regime_words(mach, word):
    assert atmosphere.regime(mach) == word


# -- forces and wall spacing --------------------------------------------------


def test_wind_axes_rotate_lift_and_drag_together():
    ax0 = physics.wind_axes(0.0)
    assert ax0["drag"] == pytest.approx((1.0, 0.0, 0.0))
    assert ax0["lift"] == pytest.approx((0.0, 1.0, 0.0))
    ax = physics.wind_axes(10.0)
    dot = sum(d * lift for d, lift in zip(ax["drag"], ax["lift"], strict=True))
    assert dot == pytest.approx(0.0, abs=1e-12)
    assert ax["drag"][1] > 0 and ax["lift"][0] < 0  # the freestream tilts up, lift tilts back
    assert ax["U"] == ax["drag"]


def test_coefficients_normalise_by_q_S_and_c():
    c = physics.coefficients(
        lift_N=200.0, drag_N=5.0, moment_Nm=-2.0, q_Pa=500.0, Sref_m2=0.8, cref_m=0.5
    )
    assert c["cl"] == pytest.approx(0.5)
    assert c["cd"] == pytest.approx(0.0125)
    assert c["cm"] == pytest.approx(-0.01)
    with pytest.raises(ValueError):
        physics.coefficients(lift_N=1, drag_N=1, moment_Nm=0, q_Pa=0, Sref_m2=1, cref_m=1)


def test_first_cell_height_follows_schlichting():
    """Re 2.05e6 (a 1 m chord at 30 m/s): Cf = (2 log10 Re - 0.65)^-2.3 is
    3.3e-3, and y+ = 1 lands the first cell centre 12 um off the wall - the
    24 um cell the O-mesh writer was measured to produce."""
    fc = physics.first_cell_height(y_plus=1.0, rho=1.225, V=30.0, L=1.0, mu=1.7894e-5)
    assert fc["Re"] == pytest.approx(2.053e6, rel=1e-3)
    assert fc["cf"] == pytest.approx(3.31e-3, rel=0.02)
    assert fc["first_cell_m"] == pytest.approx(2.4e-5, rel=0.1)
    node = physics.first_cell_height(
        y_plus=1.0, rho=1.225, V=30.0, L=1.0, mu=1.7894e-5, cell_centred=False
    )
    assert fc["first_cell_m"] == pytest.approx(2.0 * node["first_cell_m"])
    assert fc["cite"].startswith("Schlichting")
    with pytest.raises(ValueError):
        physics.first_cell_height(y_plus=0.0, rho=1.0, V=1.0, L=1.0, mu=1e-5)


# -- domain and blockage ------------------------------------------------------


def test_domain_box_multiples_and_blockage_verdicts():
    bbox = ((0.0, -0.5, -0.5), (1.0, 0.5, 0.5))  # a 1 m cube
    dom = physics.domain_3d(bbox, 1.0)
    assert dom.size()[0] == pytest.approx(21.0)  # 5 L upstream + L + 15 L downstream
    assert dom.size()[1] == pytest.approx(11.0)
    assert dom.blockage == pytest.approx(1.0 / 121.0)
    assert physics.blockage_verdict(dom.blockage) == "ok"
    assert physics.blockage_verdict(0.07) == "warn"
    assert physics.blockage_verdict(physics.domain_3d(bbox, 20.0).blockage) == "refuse"
    ground = physics.domain_3d(bbox, 1.0, ground=True)
    assert ground.zmin == pytest.approx(-0.5)  # the floor sits at the body's lowest point
    assert dom.firmness == "convention" and "ERCOFTAC" in dom.cite


# -- lifting line ---------------------------------------------------------------


def test_lifting_line_slopes_and_induced_drag():
    assert physics.cl_alpha_2d() == pytest.approx(2 * math.pi)
    assert physics.cl_alpha_3d(10.0, 0.9) == pytest.approx(5.14, rel=1e-2)  # Anderson §5.3
    assert physics.cl_alpha_3d(20.0, 0.9) == pytest.approx(5.64, rel=1e-2)
    assert physics.cl_alpha_3d(2.0) == pytest.approx(2 * math.pi / (math.sqrt(2.0) + 1.0))
    assert physics.induced_drag(0.5, 10.0, 0.9) == pytest.approx(0.25 / (math.pi * 9.0))
    with pytest.raises(ValueError):
        physics.cl_alpha_3d(0.0)


# -- sections -------------------------------------------------------------------


def test_naca_0012_and_2412_properties_match_abbott():
    p0012 = airfoil.properties(airfoil.naca4("0012", 200))
    assert p0012["max_thickness"] == pytest.approx(0.12, abs=2e-3)
    assert p0012["max_thickness_x"] == pytest.approx(0.30, abs=0.02)
    assert p0012["max_camber"] == pytest.approx(0.0, abs=1e-9)
    p2412 = airfoil.properties(airfoil.naca4("2412", 200))
    assert p2412["max_camber"] == pytest.approx(0.02, abs=1e-3)
    assert p2412["max_camber_x"] == pytest.approx(0.40, abs=0.02)


def test_naca_loop_is_ccw_closed_at_one_trailing_edge_node():
    loop = airfoil.naca4("0012", 50)
    assert len(loop) == 100  # 2n distinct points, one TE node
    assert loop[0] == (1.0, 0.0)
    assert airfoil.signed_area(loop) > 0
    assert loop.count((1.0, 0.0)) == 1
    open_te = airfoil.naca4("0012", 50, closed_te=False)
    assert len(open_te) == 101
    with pytest.raises(ValueError):
        airfoil.naca4("12", 50)
    with pytest.raises(ValueError):
        airfoil.naca4("0012", 4)


def test_selig_round_trip(tmp_path):
    loop = airfoil.naca4("4412", 30)
    path = tmp_path / "n4412.dat"
    airfoil.write_selig(path, loop, "NACA 4412")
    name, back = airfoil.read_selig(path)
    assert name == "NACA 4412"
    assert len(back) == len(loop)
    assert all(
        abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6 for a, b in zip(loop, back, strict=True)
    )


def test_ccw_keeps_the_first_point_and_flips_a_clockwise_loop():
    loop = airfoil.naca4("0012", 20)
    cw = [loop[0], *loop[1:][::-1]]
    assert airfoil.signed_area(cw) < 0
    fixed = airfoil.ccw(cw)
    assert fixed[0] == loop[0] and airfoil.signed_area(fixed) > 0


# -- STL --------------------------------------------------------------------------


def test_extruded_section_is_watertight_with_sane_areas(tmp_path):
    path = tmp_path / "wing.stl"
    n = airfoil.extrude_stl(path, airfoil.naca4("0012", 40), span=2.0, chord=0.5)
    surf = physics.read_stl(path)
    assert len(surf.tris) == n
    assert surf.watertight() == (True, 0)
    (x0, y0, z0), (x1, y1, z1) = surf.bbox
    assert (x1 - x0, z1 - z0) == pytest.approx((0.5, 2.0), rel=1e-6)
    assert y1 - y0 == pytest.approx(0.12 * 0.5, rel=0.02)
    # the prism runs along z: seen along y it is the planform, along x the
    # frontal slab, along z the section itself (NACA 0012 area 0.0817 c^2)
    assert surf.projected_area(axis=1) == pytest.approx(0.5 * 2.0, rel=0.03)
    assert surf.projected_area(axis=0) == pytest.approx(0.06 * 2.0, rel=0.05)
    assert surf.projected_area(axis=2) == pytest.approx(0.0817 * 0.25, rel=0.05)


def test_binary_stl_is_read_by_content_not_by_its_header(tmp_path):
    tris = [((0, 0, 0), (1, 0, 0), (0, 1, 0)), ((0, 0, 1), (1, 0, 1), (0, 1, 1))]
    blob = b"solid this header lies".ljust(80, b"\0") + struct.pack("<I", len(tris))
    for t in tris:
        blob += struct.pack("<3f", 0, 0, 1)
        for v in t:
            blob += struct.pack("<3f", *v)
        blob += struct.pack("<H", 0)
    path = tmp_path / "bin.stl"
    path.write_bytes(blob)
    surf = physics.read_stl(path)
    assert len(surf.tris) == 2
    assert surf.area == pytest.approx(1.0)
    assert surf.watertight()[0] is False  # two loose triangles: six open edges
    empty = tmp_path / "empty.stl"
    empty.write_text("solid x\nendsolid x\n")
    with pytest.raises(ValueError):
        physics.read_stl(empty)


def test_units_sanity_flags_a_millimetre_model_read_as_metres():
    assert physics.units_sanity(((0, 0, 0), (0.002, 0.001, 0.001))) is not None
    assert physics.units_sanity(((0, 0, 0), (500.0, 10.0, 10.0))) is not None
    assert physics.units_sanity(((0, 0, 0), (1.0, 0.4, 0.3))) is None


# -- the O-mesh -------------------------------------------------------------------


def test_omesh_has_positive_jacobians_the_asked_first_cell_and_bounded_growth():
    loop = airfoil.naca4("0012", 40)
    mesh = mesh2d.omesh(loop, first_cell=1e-4, nj=30, radius_c=20.0)
    # nj is a floor: layers are added in tens until the growth is within bounds
    assert mesh.ni == len(loop) and mesh.nj >= 30 and mesh.nj % 10 == 0
    assert mesh.cells == 80 * mesh.nj and mesh.nodes == 80 * (mesh.nj + 1)
    assert mesh.min_jacobian() > 0.0
    lo, hi = mesh.first_layer_heights()
    assert lo == pytest.approx(1e-4, rel=0.05) and hi == pytest.approx(1e-4, rel=0.05)
    assert 1.0 < mesh.growth <= 1.2
    centre = (0.5, 0.0)
    radii = [math.dist(p, centre) for p in mesh.xy[-1]]
    assert min(radii) == pytest.approx(20.0, rel=0.02) and max(radii) == pytest.approx(
        20.0, rel=0.02
    )


def test_omesh_scales_by_chord_and_refuses_a_degenerate_section():
    loop = airfoil.naca4("2412", 30)
    m1 = mesh2d.omesh(loop, first_cell=1e-3, nj=10, radius_c=10.0, chord=1.0)
    m2 = mesh2d.omesh(loop, first_cell=1e-3, nj=10, radius_c=10.0, chord=2.0)
    assert m2.xy[0][5][0] == pytest.approx(2.0 * m1.xy[0][5][0])
    # the first cell is asked for in METRES whatever the chord (the defect a
    # 1 m chord never shows: the caller used to divide by the chord too)
    small = mesh2d.omesh(loop, first_cell=1e-4, nj=20, radius_c=10.0, chord=0.3)
    assert small.first_layer_heights()[1] == pytest.approx(1e-4, rel=0.05)
    with pytest.raises(ValueError):
        mesh2d.omesh(loop[:8], first_cell=1e-3, nj=10)


def test_geometric_growth_round_trips():
    r = mesh2d.geometric_growth(distance=1.0, first=1e-3, n=40)
    assert 1e-3 * (r**40 - 1.0) / (r - 1.0) == pytest.approx(1.0, rel=1e-6)
    assert mesh2d.geometric_growth(distance=1.0, first=0.1, n=20) == 1.0  # uniform is enough


def test_su2_mesh_round_trips_its_counts_and_markers(tmp_path):
    mesh = mesh2d.omesh(airfoil.naca4("0012", 30), first_cell=2e-3, nj=12, radius_c=15.0)
    path = tmp_path / "m.su2"
    nbytes = mesh2d.write_su2(path, mesh)
    assert nbytes == path.stat().st_size
    counts = mesh2d.read_su2_counts(path)
    assert counts == {"NDIME": 2, "NELEM": mesh.cells, "NPOIN": mesh.nodes, "NMARK": 2}
    assert su2.mesh_markers(path) == ["airfoil", "farfield"]


def test_polymesh_counts_add_up_and_name_the_three_patches(tmp_path):
    from tee.windtunnel import foam

    mesh = mesh2d.omesh(airfoil.naca4("0012", 30), first_cell=2e-3, nj=12, radius_c=15.0)
    counts = mesh2d.write_polymesh(tmp_path, mesh)
    assert counts["cells"] == mesh.cells
    assert counts["points"] == 2 * mesh.nodes
    assert counts["wall_faces"] == mesh.ni and counts["far_faces"] == mesh.ni
    # every cell has a front and a back face on the empty patch
    assert counts["faces"] == counts["internal_faces"] + 2 * mesh.ni + 2 * mesh.cells
    assert counts["thickness"] == pytest.approx(0.1, rel=0.05)  # a tenth of a chord
    boundary = (tmp_path / "constant" / "polyMesh" / "boundary").read_text()
    assert foam.patch_names(boundary) == [
        ("airfoil", "wall"),
        ("farfield", "patch"),
        ("frontAndBack", "empty"),
    ]
    assert (
        "generated-by: tee.windtunnel.mesh2d" in (tmp_path / "constant/polyMesh/points").read_text()
    )


# -- the verdict ------------------------------------------------------------------


def _series(n: int, cl: float, cd: float, cm: float, decay: float = 0.93):
    residuals = {"Ux": [0.1 * decay**k for k in range(n)], "p": [0.3 * decay**k for k in range(n)]}
    coeffs = {"cl": [cl] * n, "cd": [cd] * n, "cm": [cm] * n}
    return residuals, coeffs


def test_verdict_converged_stalled_oscillating_and_insufficient():
    res, co = _series(200, 0.43, 0.011, 0.0005)
    assert verdict.verdict(res, co, ended=True)["state"] == "converged"
    stalled = {k: [max(v, 3e-3) for v in vals] for k, vals in res.items()}
    v = verdict.verdict(stalled, co, ended=True)
    assert v["state"] == "stalled" and "sat still" in v["notes"][0]
    assert verdict.verdict(stalled, co, ended=False)["state"] == "running"
    wobble = dict(co)
    wobble["cl"] = [0.43 * (1 + 0.03 * math.sin(k)) for k in range(200)]
    assert verdict.verdict(res, wobble, ended=True)["state"] == "oscillating"
    drift = dict(co)
    drift["cl"] = [0.3 + 0.001 * k for k in range(200)]
    assert verdict.verdict(res, drift, ended=True)["state"] == "insufficient"
    short = verdict.verdict(*_series(20, 0.4, 0.01, 0.0), ended=True)
    assert short["state"] == "insufficient"
    assert verdict.verdict(*_series(20, 0.4, 0.01, 0.0), ended=False)["state"] == "running"


def test_verdict_diverged_on_climbing_or_non_finite_and_error_on_fatal():
    res, co = _series(200, 0.43, 0.011, 0.0005)
    climb = dict(res)
    climb["Ux"] = [0.1 * 0.9**k for k in range(100)] + [1e-5 * 1.2**k for k in range(100)]
    v = verdict.verdict(climb, co, ended=True)
    assert v["state"] == "diverged" and "climbed back" in v["notes"][0]
    nan = dict(co)
    nan["cd"] = [0.011] * 199 + [float("nan")]
    assert verdict.verdict(res, nan, ended=True)["state"] == "diverged"
    assert verdict.verdict(res, co, ended=True, fatal=True)["state"] == "error"
    assert verdict.verdict(res, co, ended=True, cancelled=True)["state"] == "cancelled"


def test_a_near_zero_moment_does_not_break_convergence():
    """The defect the first real run found: Cm about the quarter chord of a
    symmetric section is ~5e-4, so a relative test on it flagged a converged
    run as insufficient. Below the scale floor the test is absolute."""
    res, co = _series(200, 0.43, 0.011, 0.0)
    co["cm"] = [0.0005 + 0.00002 * math.sin(k / 7.0) for k in range(200)]  # 4 % wobble, 2e-5 abs
    v = verdict.verdict(res, co, ended=True)
    assert v["state"] == "converged", v
    assert v["stationarity_pct"] < 1.0


@pytest.mark.parametrize(
    ("fid", "regime", "aoa", "state", "yplus", "trust"),
    [
        ("rans", "incompressible", 4.0, "converged", True, "comparative"),
        ("rans", "incompressible", 4.0, "converged", False, "indicative"),
        ("rans", "incompressible", 4.0, "stalled", True, "indicative"),
        ("rans", "incompressible", 14.0, "converged", True, "not-predictive"),
        ("rans", "transonic", 2.0, "converged", True, "not-predictive"),
        ("euler", "transonic", 1.25, "converged", None, "indicative"),
        ("panel", "incompressible", 6.0, "converged", None, "indicative"),
        ("panel", "incompressible", 11.0, "converged", None, "not-predictive"),
        ("rans", "incompressible", 4.0, "insufficient", True, "not-predictive"),
    ],
)
def test_uncertainty_labels_follow_the_workshop_calibration(fid, regime, aoa, state, yplus, trust):
    label = verdict.uncertainty(
        fidelity=fid, regime=regime, aoa_deg=aoa, state=state, yplus_ok=yplus
    )
    assert label["trust"] == trust
    assert label["label"] == verdict.LABELS[trust]
    assert "Drag Prediction Workshop" in label["cite"]


def test_compare_gives_drag_counts():
    d = verdict.compare(
        {"cl": 0.40, "cd": 0.0100, "cm": 0.0}, {"cl": 0.42, "cd": 0.0103, "cm": 0.001}
    )
    assert d["d_cl"] == pytest.approx(0.02)
    assert d["d_cd_counts"] == pytest.approx(3.0)


# -- the fidelity ladder ----------------------------------------------------------

ALL = {"openfoam": True, "su2": True, "vspaero": True}


@pytest.mark.parametrize(
    ("kind", "mach", "viscous", "aoa", "fid", "engine", "chosen"),
    [
        ("airfoil2d", 0.09, True, 4.0, "auto", "openfoam", "rans"),
        ("airfoil2d", 0.8, False, 1.25, "auto", "su2", "euler"),
        ("airfoil2d", 0.5, True, 2.0, "auto", "su2", "rans"),
        ("wing3d", 0.1, False, 4.0, "auto", "vspaero", "panel"),
        ("wing3d", 0.1, False, 14.0, "auto", "openfoam", "rans"),
        ("wing3d", 0.7, False, 2.0, "auto", "openfoam", "rans"),
        ("wing3d", 0.1, True, 2.0, "auto", "openfoam", "rans"),
        ("body3d", 0.05, True, 0.0, "auto", "openfoam", "rans"),
        ("adopted", 0.1, True, 0.0, "auto", "adopted", "rans"),
        ("airfoil2d", 0.1, True, 4.0, "euler", "su2", "euler"),  # an override runs
    ],
)
def test_the_router_table_one_row_at_a_time(kind, mach, viscous, aoa, fid, engine, chosen):
    c = fidelity.choose(
        kind, mach=mach, need_viscous=viscous, aoa_max_deg=aoa, fidelity=fid, available=ALL
    )
    assert (c.engine, c.fidelity) == (engine, chosen)
    assert c.reason


def test_the_router_degrades_to_what_is_installed_and_refuses_the_impossible():
    no_vsp = {"openfoam": True, "su2": True, "vspaero": False}
    c = fidelity.choose("wing3d", mach=0.1, need_viscous=False, aoa_max_deg=4.0, available=no_vsp)
    assert c.engine == "openfoam" and "absent" in c.reason
    no_foam = {"openfoam": False, "su2": True, "vspaero": True}
    c = fidelity.choose(
        "airfoil2d", mach=0.1, need_viscous=True, aoa_max_deg=4.0, available=no_foam
    )
    assert (c.engine, c.fidelity) == ("su2", "rans")
    with pytest.raises(ValueError, match="SU2"):
        fidelity.choose(
            "airfoil2d",
            mach=0.8,
            need_viscous=False,
            aoa_max_deg=1.0,
            fidelity="euler",
            available={"openfoam": True, "su2": False, "vspaero": True},
        )
    with pytest.raises(ValueError, match="bluff"):
        fidelity.choose(
            "body3d", mach=0.1, need_viscous=True, aoa_max_deg=0.0, fidelity="panel", available=ALL
        )
    with pytest.raises(ValueError, match="2-D"):
        fidelity.choose(
            "wing3d", mach=0.5, need_viscous=False, aoa_max_deg=1.0, fidelity="euler", available=ALL
        )
    with pytest.raises(ValueError):
        fidelity.choose(
            "airfoil2d",
            mach=0.1,
            need_viscous=True,
            aoa_max_deg=1.0,
            fidelity="magic",
            available=ALL,
        )


def test_cost_estimates_carry_their_measurement_date_and_gate_honestly():
    est = fidelity.estimate("openfoam", cells=16_000, iters=2000, cores=1)
    assert est["wall_s"] == pytest.approx(16_000 * 2000 * fidelity.K_ENGINE["openfoam"], rel=0.02)
    assert "2026" in est["measured_on"]
    assert fidelity.estimate("openfoam", cells=16_000, iters=2000, cores=4)[
        "wall_s"
    ] == pytest.approx(est["wall_s"] / 4, rel=0.02)
    assert fidelity.estimate("vspaero", cells=0, iters=0, sweep_points=8)[
        "wall_s"
    ] == pytest.approx(2 * fidelity.PANEL_SWEEP_S)
    assert fidelity.needs_confirmation(est, 16_000) is None
    big = fidelity.estimate("openfoam", cells=3_000_000, iters=2000, cores=4)
    assert "solver time" in fidelity.needs_confirmation(big, 3_000_000)
    assert "cells" in fidelity.needs_confirmation({"wall_s": 10, "footprint_gb": 1}, 2_500_000)
    assert "GB" in fidelity.needs_confirmation({"wall_s": 10, "footprint_gb": 9}, 100)
