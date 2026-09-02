"""P2d acceptance for partkiln.checks: validity, mass, wall, section, spec.

Every number here is from the A66 measured table (P0a) or was measured on
this Mac on 2026-09-02 while the module was written (the wall and section
figures, recorded in each module's docstring).
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln.brep import fixtures, query, shapes
from partkiln.checks import mass, section, spec, validity, wall
from partkiln.document import CommandError

pytestmark = pytest.mark.brep


def _top_face(shape):
    return next(f for f in query.faces(shape) if f.normal and f.normal[2] > 0.9)


@pytest.fixture(scope="module")
def f1():
    return fixtures.build_F1()


@pytest.fixture(scope="module")
def housing_f4():
    box = shapes.box(60, 40, 30)
    return shapes.shell(box, [_top_face(box).shape], 2.0).shape


@pytest.fixture(scope="module")
def thin_wall():
    box = shapes.box(30, 30, 10)
    return shapes.shell(box, [_top_face(box).shape], 1.2).shape


@pytest.fixture(scope="module")
def open_shell():
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing

    box = shapes.box(30, 30, 10)
    top = _top_face(box)
    sewing = BRepBuilderAPI_Sewing(1e-6)
    for f in query.faces(box):
        if f.index != top.index:
            sewing.Add(f.shape)
    sewing.Perform()
    return sewing.SewedShape()


@pytest.fixture(scope="module")
def stepped_shaft():
    a = shapes.cylinder(10, 50)
    b = shapes.cylinder(15, 30, (0, 0, 50))
    c = shapes.cylinder(10, 40, (0, 0, 80))
    fused, _ = shapes.unify(shapes.fuse([a, b, c]).shape)
    return fused


# --------------------------------------------------------------------------- hygiene


def test_import_checks_is_ocp_free() -> None:
    code = (
        "import sys, partkiln.checks, partkiln.checks.spec, partkiln.checks.wall, "
        "partkiln.checks.mass, partkiln.checks.section, partkiln.checks.validity; "
        "print('OCP' in sys.modules, 'trimesh' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == "False False"


# --------------------------------------------------------------------------- validity


def test_validate_f1_is_a_closed_valid_solid(f1) -> None:
    report = validity.validate(f1)
    assert report == {
        "valid": True,
        "problems": [],
        "solids": 1,
        "faces": 7,
        "edges": 15,
        "closed": True,
        "free_edges": 0,
    }


def test_validate_open_shell_is_not_closed_and_names_it(open_shell) -> None:
    report = validity.validate(open_shell)
    # BRepCheck calls an open shell valid (measured); closedness is ours.
    assert report["valid"] is True
    assert report["closed"] is False
    assert report["solids"] == 0
    assert report["free_edges"] == 4
    assert report["problems"] == ["not a closed solid: 0 solids, 4 free edges"]


def test_fix_reports_no_change_on_a_sound_solid(f1) -> None:
    fixed, report = validity.fix(f1)
    assert report["changed"] is False
    assert report["before"] == report["after"]
    assert shapes.volume(fixed) == pytest.approx(59214.602, abs=5e-4)


# --------------------------------------------------------------------------- mass


def test_mass_properties_f1_measured_table(f1) -> None:
    m = mass.mass_properties(f1)
    assert m["volume_mm3"] == 59214.602
    assert m["area_mm2"] == 15357.08
    assert m["com_mm"] == [50.0, 30.0, 5.0]
    assert m["bbox_mm"] == [100.0, 60.0, 10.0]
    assert m["bbox_min"] == [0.0, 0.0, 0.0]
    assert m["bbox_max"] == [100.0, 60.0, 10.0]
    assert m["material"] is None and m["honesty"] == "none"
    assert "mass_g" not in m and "inertia_kg_mm2" not in m
    # About the COM the plate's inertia is diagonal; the principal moments
    # are the diagonal sorted.
    diag = [m["inertia_mm5"][i][i] for i in range(3)]
    assert sorted(diag) == sorted(m["principal_mm5"])
    assert all(m["inertia_mm5"][i][j] == 0.0 for i in range(3) for j in range(3) if i != j)


def test_inertia_of_a_plain_box_is_the_textbook_number() -> None:
    m = mass.mass_properties(shapes.box(100, 60, 10))
    v = 60000.0
    assert m["inertia_mm5"][0][0] == pytest.approx(v * (60**2 + 10**2) / 12, abs=1e-3)
    assert m["inertia_mm5"][1][1] == pytest.approx(v * (100**2 + 10**2) / 12, abs=1e-3)
    assert m["inertia_mm5"][2][2] == pytest.approx(v * (100**2 + 60**2) / 12, abs=1e-3)


def test_mass_in_steel_f6_block_and_pin() -> None:
    block, pin = fixtures.build_F6()
    mb = mass.mass_properties(block, "steel_s275")
    mp = mass.mass_properties(pin, material="steel")
    assert (mb["mass_g"], mp["mass_g"]) == (238.869, 24.662)
    assert mb["material"] == "steel_s275" and mb["honesty"] == "standard_value"
    assert mb["density_kg_m3"] == 7850.0
    # kg mm2 = mm5 x kg/m3 x 1e-9
    assert mb["inertia_kg_mm2"][2][2] == pytest.approx(mb["inertia_mm5"][2][2] * 7850e-9, abs=1e-3)


def test_mass_density_override_wins_and_is_labelled(f1) -> None:
    m = mass.mass_properties(f1, "steel_s275", density_kg_m3=2700)
    assert m["honesty"] == "override" and m["material"] == "steel_s275"
    assert m["mass_g"] == round(59214.602 * 2700e-6, 3)
    with pytest.raises(CommandError) as err:
        mass.mass_properties(f1, "unobtainium")
    assert err.value.code == "pk_ref_unknown"
    with pytest.raises(CommandError) as err:
        mass.mass_properties(f1, density_kg_m3=-1)
    assert err.value.code == "pk_needs"


def test_mass_refuses_a_shape_with_no_volume(open_shell) -> None:
    with pytest.raises(CommandError) as err:
        mass.mass_properties(open_shell)
    assert err.value.code == "pk_needs" and "not a solid" in str(err.value)


# --------------------------------------------------------------------------- wall


def test_min_wall_f4_housing_is_2mm(housing_f4) -> None:
    assert shapes.volume(housing_f4) == pytest.approx(15552.0, abs=1e-6)
    assert shapes.counts(housing_f4)["faces"] == 11
    t = time.perf_counter()
    w = wall.min_wall(housing_f4)
    dt = time.perf_counter() - t
    assert w["min_mm"] == pytest.approx(2.0, abs=0.01)
    assert w["method"] == "ray" and w["faces"] == 11
    assert w["hits"] == w["samples"] == 250  # 11 faces x 25, minus none: every ray hits
    assert w["face"]["type"] == "plane" and w["hit_face"]["type"] == "plane"
    assert len(w["at"]) == 3
    assert all(p["mm"] == 2.0 for p in w["pairs"])
    assert dt < 0.5, f"F4 ray scan took {dt:.3f} s (measured 4 ms)"


def test_min_wall_mesh_estimate_agrees_and_says_estimate(housing_f4) -> None:
    w = wall.min_wall(housing_f4, method="mesh")
    assert w["method"] == "mesh" and w["estimate"] is True
    assert w["min_mm"] == pytest.approx(2.0, abs=0.02)


def test_min_wall_f1_is_the_plate_thickness(f1) -> None:
    assert wall.min_wall(f1)["min_mm"] == 10.0


def test_min_wall_f5_100_holes_under_budget() -> None:
    f5 = fixtures.build_F5()
    t = time.perf_counter()
    w = wall.min_wall(f5)
    dt = time.perf_counter() - t
    assert w["min_mm"] == 12.0  # plate thickness; hole pitch leaves 12 mm webs too
    assert dt < 2.0, f"F5 ray scan took {dt:.3f} s (measured 0.12 s for 2 650 rays)"


def test_check_wall_finds_a_1_2mm_wall_under_a_2mm_limit(thin_wall) -> None:
    assert shapes.volume(thin_wall) == pytest.approx(2296.512, abs=1e-6)
    r = wall.check_wall(thin_wall, limit_mm=2)
    assert r["ok"] is False and r["min_mm"] == 1.2 and r["limit_mm"] == 2.0
    (v,) = r["violations"]
    assert v["rule"] == "min_wall_mm" and v["got"] == 1.2 and v["limit"] == 2.0
    assert v["fix"].startswith("increase min wall to 2 mm at [")
    assert wall.check_wall(thin_wall, limit_mm=1.0)["ok"] is True


def test_min_wall_refusals(open_shell, f1) -> None:
    with pytest.raises(CommandError) as err:
        wall.min_wall(open_shell)
    assert err.value.code == "pk_needs" and "no solid" in str(err.value)
    with pytest.raises(CommandError) as err:
        wall.min_wall(f1, method="guess")
    assert err.value.code == "pk_bad_op" and "ray, mesh" in str(err.value)
    with pytest.raises(CommandError) as err:
        wall.check_wall(f1, limit_mm=0)
    assert err.value.code == "pk_needs"


# --------------------------------------------------------------------------- section


def test_section_f1_at_x50_is_500_in_two_faces(f1) -> None:
    s = section.section_area(f1, (50, 0, 0), (1, 0, 0))
    # 60 x 10 band minus the 10 x 10 strip through the hole axis = two 25 x 10.
    assert s["area_mm2"] == 500.0
    assert s["faces"] == 2 and s["loops"] == 2
    assert s["per_face"] == [250.0, 250.0]
    # Off the hole the band is whole: 600.
    assert section.section_area(f1, (20, 0, 0), (1, 0, 0))["area_mm2"] == 600.0


def test_section_stepped_shaft_is_2700(stepped_shaft) -> None:
    assert shapes.volume(stepped_shaft) == pytest.approx(49480.084, abs=5e-4)
    assert shapes.counts(stepped_shaft)["faces"] == 7
    s = section.section_area(stepped_shaft, (0, 0, 0), (0, 1, 0))
    assert s["area_mm2"] == 2700.0 and s["faces"] == 1
    # A cross-section through the d30 step is the full disc.
    disc = section.section_area(stepped_shaft, (0, 0, 65), (0, 0, 1))
    assert disc["area_mm2"] == pytest.approx(706.858, abs=5e-4)


def test_section_refusals(f1) -> None:
    with pytest.raises(CommandError) as err:
        section.section_area(f1, (500, 0, 0), (1, 0, 0))
    assert err.value.code == "pk_no_effect" and "misses the shape" in str(err.value)
    with pytest.raises(CommandError) as err:
        section.section_area(f1, (50, 0, 0), (0, 0, 0))
    assert err.value.code == "pk_needs"


# --------------------------------------------------------------------------- spec


def test_check_spec_passes_f1_on_every_rule(f1) -> None:
    result = spec.check_spec(
        f1,
        {
            "bbox": [100, "60mm", 10],
            "volume_mm3": [59000, 59500],
            "mass_g": {"min": 464, "max": 465},
            "holes": [{"dia": 10, "count": 1}],
            "min_wall_mm": "5mm",
            "valid": True,
            "watertight": True,
            "faces": 7,
            "edges": 15,
        },
        material="steel_s275",
    )
    assert result["verdict"] == "pass" and result["violations"] == []
    assert result["checked"] == list(spec.RULES)
    assert result["material"] == "steel_s275"


def test_check_spec_fails_with_the_violation_shape(thin_wall) -> None:
    result = spec.check_spec(
        thin_wall,
        {"min_wall_mm": 2, "bbox": [30, 30, 12], "holes": [{"dia": 10}], "faces": 6},
    )
    assert result["verdict"] == "fail"
    by_rule = {v["rule"]: v for v in result["violations"]}
    assert set(by_rule) == {"min_wall_mm", "bbox", "holes", "faces"}
    for v in result["violations"]:
        assert {"rule", "got", "limit", "fix"} <= set(v) and v["fix"]
    assert by_rule["min_wall_mm"]["got"] == 1.2 and by_rule["min_wall_mm"]["limit"] == 2.0
    assert by_rule["min_wall_mm"]["fix"].startswith("increase min wall to 2 mm at [")
    assert by_rule["bbox"]["axis"] == "Z" and by_rule["bbox"]["got"] == 10.0
    assert by_rule["holes"]["got"] == 0 and by_rule["holes"]["limit"] == 1
    assert by_rule["faces"]["got"] == 11 and by_rule["faces"]["limit"] == 6


def test_check_spec_watertight_fails_on_an_open_shell(open_shell) -> None:
    result = spec.check_spec(open_shell, {"valid": True, "watertight": True})
    assert result["verdict"] == "fail"
    (v,) = result["violations"]
    assert v["rule"] == "watertight" and "4 free edges" in v["fix"]


def test_check_spec_counts_holes_by_unique_cylindrical_faces() -> None:
    f5 = fixtures.build_F5()
    ok = spec.check_spec(f5, {"holes": [{"dia": 8, "count": 100}]})
    assert ok["verdict"] == "pass"
    bad = spec.check_spec(f5, {"holes": [{"dia": 8, "count": 99}, {"dia": 6, "count": 1}]})
    assert [v["got"] for v in bad["violations"]] == [100, 0]
    assert "seats count under their own diameter" in bad["violations"][0]["fix"]


def test_check_spec_parts_list_is_one_compound() -> None:
    block, pin = fixtures.build_F6()
    # 30 429.204 + 3 141.593 mm3; 7 + 3 unique faces.
    result = spec.check_spec([block, pin], {"volume_mm3": [33570, 33571], "faces": 10})
    assert result["verdict"] == "pass"


def test_check_spec_refusals(f1) -> None:
    with pytest.raises(CommandError) as err:
        spec.check_spec(f1, {"bbox": [100, 60, 10], "colour": "red"})
    assert err.value.code == "pk_bad_op"
    assert "colour" in str(err.value) and "min_wall_mm" in str(err.value)
    with pytest.raises(CommandError) as err:
        spec.check_spec(f1, {"mass_g": [1, 2]})
    assert err.value.code == "pk_needs" and "steel_s275" in str(err.value)
    with pytest.raises(CommandError) as err:
        spec.check_spec(f1, {"volume_mm3": 59214})
    assert err.value.code == "pk_bad_op"
    with pytest.raises(CommandError) as err:
        spec.check_spec([], {"faces": 7})
    assert err.value.code == "pk_needs"
