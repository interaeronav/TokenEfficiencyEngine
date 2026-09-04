"""P2d acceptance for partkiln.checks: validity, mass, wall, section, spec.

Every number here is from the A66 measured table (P0a) or was measured on
this Mac on 2026-09-02 while the module was written (the wall and section
figures, recorded in each module's docstring).
"""

from __future__ import annotations

import math
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
def near_edge_bore():
    """A 100x60x10 plate whose one d10 bore leaves 0.600 mm to the x=100 face.

    100 - (94.4 + 5) = 0.6. The thinnest generatrix of the bore is a single
    line in u, so a UV CELL-CENTRE grid never lands on it: measured
    2026-09-04 the grid alone reports 1.922 mm at n=5 and is non-monotone in
    n (n=7 1.216, n=9 0.645, n=13 0.768, n=21 0.608) - raising the sample
    count is not a fix, which is why `min_wall` also runs face-pair extrema.
    """
    return shapes.cut(shapes.box(100, 60, 10), [shapes.cylinder(5, 12, (94.4, 24, -1))]).shape


@pytest.fixture(scope="module")
def wedge():
    """A prism whose section tapers to a 0.2 mm heel at x=0 (true min wall 0.2).

    The thin spot is ON the boundary of both faces that bound it, so no
    interior sample of either can reach it; the face-pair extrema solution
    lands exactly there (it is `IsOnEdge`, hence the projection back to (u, v)).
    """
    face = shapes.make_face_from_points([(0, 0, 0), (40, 0, 0), (40, 0, 5.0), (0, 0, 0.2)])
    return shapes.prism(face, (0, 60, 0)).shape


@pytest.fixture(scope="module")
def filleted_plate():
    """A 100x60x10 plate with two d6 holes and four r3 corner fillets.

    Six cylindrical faces of radius 3, of which only the two holes are
    concave from the material's side - the spec's `holes` rule must count 2.
    """
    plate = shapes.cut(
        shapes.box(100, 60, 10),
        [shapes.cylinder(3, 12, (25, 30, -1)), shapes.cylinder(3, 12, (75, 30, -1))],
    ).shape
    corners = [
        e.shape
        for e in query.edges(plate)
        if e.curve_type == "line" and e.direction and abs(e.direction[2]) > 0.9
    ]
    return shapes.fillet(plate, corners, 3.0).shape


@pytest.fixture(scope="module")
def pocket_r5():
    """A 100x60x10 plate with a 40x20x5 pocket whose corners are r5 - and NO HOLES.

    Four CONCAVE cylindrical faces of d10 (the material really is outside a
    corner radius) each sweeping exactly 90 degrees. Counting concave faces
    called this part four Ø10 holes; a hole table has never tabled one.
    """
    plate = shapes.cut(shapes.box(100, 60, 10), [shapes.box(40, 20, 6, (30, 20, 5))]).shape
    corners = [
        e.shape
        for e in query.edges(plate)
        if e.curve_type == "line"
        and e.direction
        and abs(e.direction[2]) > 0.9
        # the pocket's own verticals, not the plate's four outside ones
        and 30 - 1e-6 <= e.midpoint[0] <= 70 + 1e-6
        and 20 - 1e-6 <= e.midpoint[1] <= 40 + 1e-6
    ]
    assert len(corners) == 4
    return shapes.fillet(plate, corners, 5.0).shape


def _drilled_from_both_faces(thickness: float, depth: float = 5.0):
    """A 100x60 plate with a coaxial d10 blind hole `depth` deep from each face.

    At 30 mm thick that is TWO holes with 20 mm of metal standing between them;
    at 10 mm the two cuts meet and it is ONE Ø10 bore that reaches the face
    list as two walls. Same construction, two answers, and the metal decides.
    """
    return shapes.cut(
        shapes.box(100, 60, thickness),
        [
            shapes.cylinder(5, depth, (50, 30, thickness - depth)),
            shapes.cylinder(5, depth, (50, 30, 0)),
        ],
    ).shape


@pytest.fixture(scope="module")
def slotted_plate():
    """A 100x60x10 plate with one 40 x 8 through slot, cut by a fused tool.

    Its two end cylinders are genuine concave d8 walls that each close half a
    turn, joined to the flats by tangent edges: a slot, not two holes.
    """
    tool, _ = shapes.unify(
        shapes.fuse(
            [
                shapes.box(32, 8, 12, (34, 26, -1)),
                shapes.cylinder(4, 12, (34, 30, -1)),
                shapes.cylinder(4, 12, (66, 30, -1)),
            ]
        ).shape
    )
    return shapes.cut(shapes.box(100, 60, 10), [tool]).shape


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


def test_validate_a_sphere_and_a_cone_are_closed_solids() -> None:
    """A degenerate edge is not a free edge (defect: the pole seam and the cone
    apex have ONE ancestor face, so counting them called a closed solid open)."""
    for solid, faces in ((shapes.sphere(10), 1), (shapes.cone(8, 0, 20), 2)):
        report = validity.validate(solid)
        assert report["valid"] is True and report["solids"] == 1
        assert report["faces"] == faces
        assert report["free_edges"] == 0
        assert report["closed"] is True
        assert report["problems"] == []


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
    # trimesh.proximity.thickness builds an R-tree index; rtree is the [mesh]
    # extra, absent from this venv (measured 2026-09-04), so this is a skip
    # naming the extra, never a silent pass.
    pytest.importorskip("rtree", reason="trimesh.proximity.thickness needs partkiln[mesh]")
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


def test_min_wall_mesh_refuses_when_rtree_is_absent(housing_f4, monkeypatch) -> None:
    """A missing optional dependency is a refusal with the install line, never a
    bare ModuleNotFoundError three frames down inside trimesh (D8)."""
    monkeypatch.setitem(sys.modules, "rtree", None)  # `import rtree` -> ImportError
    with pytest.raises(CommandError) as err:
        wall.min_wall(housing_f4, method="mesh")
    assert err.value.code == "pk_not_served"
    message = str(err.value)
    assert "rtree" in message and "partkiln[mesh]" in message
    assert "method='ray'" in message


def test_min_wall_measures_a_wall_no_uv_sample_lands_on(near_edge_bore) -> None:
    """The 0.600 mm web between the bore and the x=100 face, which the UV grid
    reports as 1.922 at n=5 and never converges to by raising n."""
    w = wall.min_wall(near_edge_bore)
    assert w["min_mm"] == 0.6
    assert w["pairs_examined"] >= 1
    assert w["face"]["type"] in ("cylinder", "plane")
    for n in (5, 9, 21):
        assert wall.min_wall(near_edge_bore, samples_per_face=n)["min_mm"] == 0.6
    r = wall.check_wall(near_edge_bore, limit_mm=1.5)
    assert r["ok"] is False and r["min_mm"] == 0.6
    assert spec.check_spec(near_edge_bore, {"min_wall_mm": 1.5})["verdict"] == "fail"


def test_min_wall_measures_a_wedge_heel_on_the_face_boundary(wedge) -> None:
    assert shapes.volume(wedge) == pytest.approx(6240.0, abs=1e-6)
    assert wall.min_wall(wedge)["min_mm"] == 0.2


def test_min_wall_pair_pass_is_gated_and_says_when_it_gave_up(near_edge_bore, monkeypatch) -> None:
    """The O(faces^2) pass is capped by face count and by extrema solves; a
    capped answer says so rather than quietly reporting the grid's 1.922 mm as
    if it were the wall."""
    monkeypatch.setattr(wall, "FACE_CAP", 3)
    w = wall.min_wall(near_edge_bore)
    assert w["faces"] == 7 and w["pairs_examined"] == 0
    assert w["pairs_capped"] is True and w["min_mm"] == 1.922
    monkeypatch.setattr(wall, "FACE_CAP", 400)
    monkeypatch.setattr(wall, "PAIR_CAP", 0)
    capped = wall.min_wall(near_edge_bore)
    assert capped["pairs_capped"] is True and capped["min_mm"] == 1.922


def test_min_wall_ray_says_the_minimum_is_not_proven(f1) -> None:
    """The search is a sampler plus a pruned face-pair pass: it can only ever
    report an UPPER bound, so it labels itself and check_spec repeats it."""
    w = wall.min_wall(f1)
    assert w["min_mm"] == 10.0
    assert w["estimate"] is True and w["proven"] is False
    assert w["samples_per_face"] == 5 and w["faces"] == 7
    result = spec.check_spec(f1, {"min_wall_mm": 5})
    assert result["verdict"] == "pass"
    (note,) = result["unproven"]
    assert note.startswith("min_wall_mm") and "upper bound" in note
    assert "5x5" in note


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
            # F1's one bore is a hole and nothing else: no slot of any width.
            "slots": [{"width": 10, "count": 0}],
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


def test_check_spec_counts_a_hole_per_hole_on_f5() -> None:
    """One row per hole, a hundred times, and unchanged by the shared predicate."""
    f5 = fixtures.build_F5()
    ok = spec.check_spec(f5, {"holes": [{"dia": 8, "count": 100}]})
    assert ok["verdict"] == "pass"
    bad = spec.check_spec(f5, {"holes": [{"dia": 8, "count": 99}, {"dia": 6, "count": 1}]})
    assert [v["got"] for v in bad["violations"]] == [100, 0]
    assert "seats count under their own diameter" in bad["violations"][0]["fix"]


def test_check_spec_does_not_count_fillets_as_holes(filleted_plate) -> None:
    """A fillet of the hole's radius is a CONVEX cylinder; only a concave one is
    a hole. Six r3 cylinders, two holes - the correct part must pass its spec."""
    radii = [f.radius for f in query.faces(filleted_plate) if f.surface_type == "cylinder"]
    assert len(radii) == 6 and all(r == pytest.approx(3.0) for r in radii)
    assert spec.check_spec(filleted_plate, {"holes": [{"dia": 6, "count": 2}]})["verdict"] == "pass"
    bad = spec.check_spec(filleted_plate, {"holes": [{"dia": 6, "count": 6}]})
    (v,) = bad["violations"]
    assert v["got"] == 2 and v["limit"] == 6
    assert "concave" in v["fix"] and "fillet" in v["fix"]


# ----------------------------------------------------- holes counts what a table tables


def test_check_spec_does_not_call_a_pocket_corner_radius_a_hole(pocket_r5) -> None:
    """The defect, on the part that shows it plainest: a pocket with NO holes.

    `holes` counted CONCAVE CYLINDRICAL FACES, and a corner radius is concave -
    the material really is outside it. Measured 2026-09-04 on the old rule, a
    40 x 20 pocket with r5 corners and not one hole in the part answered:

        holes: [{dia: 10, count: 4}]  ->  verdict: pass
        holes: [{dia: 10, count: 0}]  ->  verdict: fail, "found 4"

    while `pk_drawing` tabled nothing for the same solid. A check that
    confidently returns the wrong verdict is the worst thing this kernel can
    do, and a check that contradicts the sheet is indefensible to whoever is
    holding both. Both now answer from `brep.holes`.
    """
    cylinders = [f for f in query.faces(pocket_r5) if f.surface_type == "cylinder"]
    assert len(cylinders) == 4  # the corner radii really are there,
    assert all(shapes.is_concave_cylinder(f.shape) for f in cylinders)  # and really concave,
    assert [round(shapes.cylinder_sweep_deg(f.shape), 6) for f in cylinders] == [90.0] * 4

    assert spec.check_spec(pocket_r5, {"holes": [{"dia": 10, "count": 0}]})["verdict"] == "pass"
    bad = spec.check_spec(pocket_r5, {"holes": [{"dia": 10, "count": 4}]})
    assert bad["verdict"] == "fail"
    (v,) = bad["violations"]
    assert v["got"] == 0 and v["limit"] == 4
    assert "found 0" in v["fix"] and "never close a full turn" in v["fix"]


def test_check_spec_counts_a_bore_split_into_two_walls_once() -> None:
    """5 + 5 through a 10 mm plate is ONE Ø10 hole, not two.

    Two faces, one bore: the cuts meet, so there is no metal between them and
    the walls merge. `depth` reads THRU because the union spans the body.
    """
    plate = _drilled_from_both_faces(10.0)
    assert sum(1 for f in query.faces(plate) if f.surface_type == "cylinder") == 2
    assert spec.check_spec(plate, {"holes": [{"dia": 10, "count": 1}]})["verdict"] == "pass"
    two = spec.check_spec(plate, {"holes": [{"dia": 10, "count": 2}]})
    assert two["verdict"] == "fail" and two["violations"][0]["got"] == 1


def test_check_spec_counts_two_blind_holes_with_metal_between_them_as_two() -> None:
    """The same construction through 30 mm leaves 20 mm of solid: TWO holes.

    Coaxial and equal-radius is not enough to merge - a sheet that merged
    these would send a drill through a standing wall - so the midpoint of the
    gap is classified and the metal decides.
    """
    plate = _drilled_from_both_faces(30.0)
    removed = 100.0 * 60.0 * 30.0 - mass.mass_properties(plate)["volume_mm3"]
    assert removed == pytest.approx(2.0 * math.pi * 25.0 * 5.0, abs=1e-3)  # both holes, no more
    assert spec.check_spec(plate, {"holes": [{"dia": 10, "count": 2}]})["verdict"] == "pass"
    one = spec.check_spec(plate, {"holes": [{"dia": 10, "count": 1}]})
    assert one["verdict"] == "fail" and one["violations"][0]["got"] == 2


def test_check_spec_does_not_count_a_slots_two_ends_as_holes(slotted_plate) -> None:
    """A BEHAVIOUR CHANGE, and a deliberate one: `holes` used to count 2 per slot.

    A slot's ends are genuine concave d8 walls and `2x Ø8` was never a false
    number - but a drafter dimensions a slot as a slot, `pk_drawing` prints one
    `40 x 8 SLOT THRU` row, and the two tools must not disagree. `slots` is
    where a slot is checked now, and the refusal says so.
    """
    ends = [f for f in query.faces(slotted_plate) if f.surface_type == "cylinder"]
    assert len(ends) == 2 and all(shapes.is_concave_cylinder(f.shape) for f in ends)

    assert spec.check_spec(slotted_plate, {"holes": [{"dia": 8, "count": 0}]})["verdict"] == "pass"
    bad = spec.check_spec(slotted_plate, {"holes": [{"dia": 8, "count": 2}]})
    (v,) = bad["violations"]
    assert v["got"] == 0 and "2 slot end(s) of d8" in v["fix"] and "slots rule" in v["fix"]


def test_check_spec_slots_measures_width_and_length(slotted_plate) -> None:
    """Width is the end diameter, length the overall cut - both read from the
    model, by the same `brep.holes.slot_size` the sheet's SLOT row prints."""
    assert spec.check_spec(slotted_plate, {"slots": [{"width": 8, "length": 40}]})["verdict"] == (
        "pass"
    )
    # length is optional: every slot of that width.
    assert spec.check_spec(slotted_plate, {"slots": [{"width": 8}]})["verdict"] == "pass"
    assert spec.check_spec(slotted_plate, {"slots": [{"width": "8mm", "count": 1}]})["verdict"] == (
        "pass"
    )
    wrong = spec.check_spec(slotted_plate, {"slots": [{"width": 8, "length": 50}]})
    assert wrong["verdict"] == "fail"
    (v,) = wrong["violations"]
    assert v["got"] == 0 and v["width"] == 8.0 and v["length"] == 50.0
    assert "[[8.0, 40.0]]" in v["fix"]


def test_check_spec_slots_finds_none_where_two_holes_share_a_radius() -> None:
    """Two d8 holes 40 mm apart are not a 40 x 8 slot: nothing walls them
    together, and inventing a slot is the mirror of inventing a hole."""
    pair = shapes.cut(
        shapes.box(100, 60, 10),
        [shapes.cylinder(4, 12, (34, 30, -1)), shapes.cylinder(4, 12, (66, 30, -1))],
    ).shape
    assert spec.check_spec(pair, {"holes": [{"dia": 8, "count": 2}]})["verdict"] == "pass"
    none = spec.check_spec(pair, {"slots": [{"width": 8, "length": 40}]})
    assert none["verdict"] == "fail"
    assert (
        none["violations"][0]["got"] == 0
        and "slots present as [width, length]: []" in (none["violations"][0]["fix"])
    )


def test_check_spec_slots_refuses_a_bad_row_with_the_fix(f1) -> None:
    for bad in (
        {"slots": "wide"},
        {"slots": [{"length": 40}]},
        {"slots": [{"width": 8, "count": "two"}]},
    ):
        with pytest.raises(CommandError) as err:
            spec.check_spec(f1, bad)
        assert err.value.code == "pk_bad_op", bad
        assert "Fix:" in str(err.value), bad


def test_check_spec_refuses_a_bad_limit_instead_of_a_raw_valueerror(f1) -> None:
    """User input never escapes as ValueError: every coercion is a refusal with
    a D8 code and the fix (D8)."""
    for bad in (
        {"volume_mm3": ["big", 10]},
        {"faces": "seven"},
        {"holes": [{"dia": 6, "count": "two"}]},
        {"min_wall_mm": 1, "wall_samples": "lots"},
        {"mass_g": [1, 2], "density_kg_m3": "steelish"},
    ):
        with pytest.raises(CommandError) as err:
            spec.check_spec(f1, bad)
        assert err.value.code == "pk_bad_op", bad
        assert "Fix:" in str(err.value), bad


def test_check_spec_reads_lengths_in_the_documents_unit(f1) -> None:
    """Law 12 at the spec boundary: a bare number is the DOCUMENT's unit, and
    `strict_units` refuses it. F1 is 100 x 60 x 10 mm = 3.937 x 2.362 x 0.394 in."""
    inches = spec.check_spec(
        f1, {"bbox": [3.937008, 2.362205, 0.393701], "min_wall_mm": 0.3}, units="in"
    )
    assert inches["verdict"] == "pass"
    fails = spec.check_spec(f1, {"bbox": [100, 60, 10]}, units="in")
    assert fails["verdict"] == "fail" and len(fails["violations"]) == 3

    class _Doc:
        units = "in"
        strict_units = False

    assert spec.check_spec(f1, {"bbox": [3.937008, 2.362205, 0.393701]}, units=_Doc())["verdict"]

    class _Strict:
        units = "mm"
        strict_units = True

    with pytest.raises(CommandError) as err:
        spec.check_spec(f1, {"min_wall_mm": 5}, units=_Strict())
    assert err.value.code == "pk_unitless"
    # A string carries its own unit, so it passes even under strict_units.
    assert spec.check_spec(f1, {"min_wall_mm": "5mm"}, units=_Strict())["verdict"] == "pass"
    with pytest.raises(CommandError) as err:
        spec.check_spec(f1, {"min_wall_mm": 5}, units="furlong")
    assert err.value.code == "pk_unit_unknown"


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
