"""Phase 11: sketch solving, material facts, plausibility, tier-0 checks."""

from __future__ import annotations

import pytest

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.physical import materials, plaus
from tee.physical.sketch import solve_sketch
from tee.physical.verify import sim_readiness, tier0

# -- sketch_solve -----------------------------------------------------------

RECT = {
    "points": [
        {"id": "a", "at": [0.1, 0.1], "fixed": True},
        {"id": "b", "at": [3.9, 0.2]},
        {"id": "c", "at": [4.1, 2.8]},
        {"id": "d", "at": [-0.1, 3.1]},
    ],
    "lines": [
        {"id": "ab", "from": "a", "to": "b"},
        {"id": "bc", "from": "b", "to": "c"},
        {"id": "cd", "from": "c", "to": "d"},
        {"id": "da", "from": "d", "to": "a"},
    ],
    "constraints": [
        {"kind": "distance", "a": "a", "b": "b", "value": 4.0},
        {"kind": "distance", "a": "b", "b": "c", "value": 3.0},
        {"kind": "horizontal", "line": "ab"},
        {"kind": "vertical", "line": "bc"},
        {"kind": "horizontal", "line": "cd"},
        {"kind": "vertical", "line": "da"},
    ],
}


def test_sketch_closes_dimensioned_rectangle():
    out = solve_sketch(RECT)
    assert out["ok"]
    points = out["points"]
    assert points["b"][0] - points["a"][0] == pytest.approx(4.0, abs=1e-4)
    assert points["c"][1] - points["b"][1] == pytest.approx(3.0, abs=1e-4)
    assert points["b"][1] == pytest.approx(points["a"][1], abs=1e-4)


def test_sketch_over_constrained_names_conflict():
    """Acceptance: over-constrained fixture answers with exact-fix errors."""
    bad = {
        **RECT,
        "constraints": [
            *RECT["constraints"],
            {"kind": "distance", "a": "a", "b": "b", "value": 5.0},  # contradicts 4.0
        ],
    }
    with pytest.raises(TeeError) as err:
        solve_sketch(bad)
    assert err.value.code == "over_constrained"
    assert "distance" in err.value.message  # names the constraint kind
    assert "remove or correct" in (err.value.fix or "")


def test_sketch_under_constrained_reports_dof():
    loose = {
        "points": RECT["points"],
        "lines": RECT["lines"],
        "constraints": [{"kind": "distance", "a": "a", "b": "b", "value": 4.0}],
    }
    out = solve_sketch(loose)
    assert out["ok"] and "under_constrained" in out
    assert "degrees of freedom" in out["under_constrained"]


def test_sketch_polygon_output():
    from tee.physical.sketch import polygon_from

    out = solve_sketch(RECT)
    polygon = polygon_from(out["points"], ["a", "b", "c", "d"])
    assert len(polygon) == 4


def test_sketch_unknown_point_reference():
    bad = {**RECT, "constraints": [{"kind": "distance", "a": "a", "b": "zz", "value": 1}]}
    with pytest.raises(TeeError) as err:
        solve_sketch(bad)
    assert err.value.code == "unknown_point"


# -- material facts ---------------------------------------------------------


def test_material_three_tiers_honesty_labeled():
    facts = materials.facts("concrete")
    assert facts["material"] == "concrete_c25"
    density = facts["physics"]["density"]
    assert density["value"] == 2400 and "EN 1991" in density["source"]
    assert density["honesty"] == "standard_value"
    assert facts["engineering"]["fck"]["value"] == 25
    assert "bullet_friction" in facts["engine_caveats"]


def test_material_render_tier_from_phase9():
    facts = materials.facts("steel")
    # the render tier rides the Phase 9 measured dataset
    assert "render" in facts
    assert facts["render"]["provenance"]["honesty"] == "measured"


def test_mat_assign_ops_sqrt_friction_and_mass():
    ops, fact = materials.assign_ops("e1", "timber", volume_m3=0.5)
    props = ops[0]["props"]
    assert props["physics_density_kg_m3"] == 420
    # Bullet multiplies pair coefficients: bodies carry sqrt(mu)
    assert props["physics_friction_body"] == pytest.approx(0.45**0.5, abs=1e-3)
    assert fact["mass_kg"] == pytest.approx(210.0)
    assert "Bullet multiplies" in fact["friction_note"]


def test_banned_bulk_sources_stay_out():
    """The banned list exists AND no data file cites a banned source."""
    import json
    from importlib import resources

    banned = ("MatWeb", "MakeItFrom", "NIST SRD", "ArcSim")
    assert all(any(b in s for s in materials.banned_sources()) for b in banned)
    for pkg, name in (("tee.physical", "data/materials_eng.json"),):
        data = json.loads(resources.files(pkg).joinpath(name).read_text())
        for key, mat in data["materials"].items():
            for tier in ("physics", "engineering"):
                for leaf_name, leaf in mat.get(tier, {}).items():
                    source = leaf.get("source", "")
                    assert not any(b.lower() in source.lower() for b in banned), (
                        f"{key}.{tier}.{leaf_name} cites a banned source"
                    )


def test_unknown_material_names_alternatives():
    with pytest.raises(TeeError) as err:
        materials.find("unobtanium")
    assert "concrete" in (err.value.fix or "")


# -- plausibility -----------------------------------------------------------


def _clean_model():
    return {
        "elements": [
            {"id": "f1", "class": "footing", "width_m": 0.5, "wall": "w1"},
            {
                "id": "w1",
                "class": "wall",
                "bearing": True,
                "height_m": 2.7,
                "thickness_m": 0.22,
                "material": "brick",
                "supports": ["f1"],
            },
            {"id": "j1", "class": "joist", "size": "2x10", "span_m": 3.2, "supports": ["w1"]},
            {"id": "o1", "class": "opening", "wall": "w1", "width_m": 0.9, "has_header": True},
            {"id": "r1", "class": "roof", "covering": "concrete_tile", "pitch_deg": 35.0},
            {"id": "room1", "class": "room", "ceiling_m": 2.6, "habitable": True},
            {
                "id": "s1",
                "class": "stair",
                "riser_mm": 180,
                "tread_mm": 280,
                "headroom_mm": 2100,
                "width_mm": 950,
            },
        ]
    }


def test_plaus_clean_reports_rule_count_never_passes():
    out = plaus.check(_clean_model())
    assert out["findings"] == []
    assert "no plausibility conflicts detected" in out["summary"]
    assert "rules evaluated" in out["summary"]
    assert "not an approval" in out["disclaimer"]
    assert "passes" not in str(out).lower().replace("no plausibility", "")


def test_plaus_flags_overspan_joist_citing_table():
    """Acceptance: seeded over-span joist cites the table."""
    model = _clean_model()
    model["elements"][2]["span_m"] = 4.5  # 2x10 worst-grade envelope 3.35
    out = plaus.check(model)
    hits = [f for f in out["findings"] if f["rule"] == "joist_span_max_m"]
    assert hits and "IRC R502.3.1" in hits[0]["source"]
    assert "delta +1.15" in hits[0]["detail"]
    assert hits[0]["severity"] == "CODE"


def test_plaus_flags_low_tile_roof():
    """Acceptance: tile roof below 30 deg - the Okongo check."""
    model = _clean_model()
    model["elements"][4]["pitch_deg"] = 20.0
    out = plaus.check(model)
    hits = [f for f in out["findings"] if f["rule"] == "roof_pitch_min_deg"]
    assert hits and "BS 5534" in hits[0]["source"]
    assert "20.0 deg < 30.0" in hits[0]["detail"]


def test_plaus_flags_broken_load_path():
    """Acceptance: broken load path anchored on IRC R301.1."""
    model = _clean_model()
    model["elements"][1]["supports"] = []  # wall floats structurally
    out = plaus.check(model)
    hits = [f for f in out["findings"] if f["rule"] == "load_path"]
    assert hits and "LOAD_PATH_BROKEN" in hits[0]["detail"]
    assert hits[0]["source"] == "IRC R301.1"
    assert hits[0]["severity"] == "CODE"


def test_plaus_missing_header_and_stairs():
    model = _clean_model()
    model["elements"][3]["has_header"] = False
    model["elements"][6]["riser_mm"] = 210
    out = plaus.check(model)
    rules = {f["rule"] for f in out["findings"]}
    assert "header_required" in rules
    assert "stairs" in rules


def test_plaus_never_emits_member_size():
    model = _clean_model()
    model["elements"][2]["span_m"] = 6.0
    out = plaus.check(model)
    text = str(out["findings"]).lower()
    # findings state the delta, never prescribe a member
    assert "use a 2x12" not in text and "increase to" not in text


# -- tier 0 -----------------------------------------------------------------


def _app_with(tmp_path, entities):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    ops = [
        {"op": "create", "kind": "object", "name": name, "props": props} for name, props in entities
    ]
    out = app.run_batch("fake", ops)
    return app, out["created"]


def test_tier0_floating_chair_caught(tmp_path):
    """Acceptance: a seeded floating chair is caught by Tier 0."""
    app, _ = _app_with(
        tmp_path,
        [
            ("floor", {"location": [0, 0, -0.1], "dims_m": [10, 10, 0.1]}),
            ("chair", {"location": [1, 1, 0.4], "dims_m": [0.5, 0.5, 0.9]}),
        ],
    )
    out = tier0(app, "fake")
    facts = [f for f in out["facts"] if f["kind"] == "floating"]
    assert facts and facts[0]["gap_m"] == pytest.approx(0.4)


def test_tier0_unsupported_com_stack_caught(tmp_path):
    """Acceptance: an unsupported-CoM stack is caught cumulatively."""
    app, _ = _app_with(
        tmp_path,
        [
            ("base", {"location": [0, 0, 0], "dims_m": [0.4, 0.4, 0.4]}),
            ("top", {"location": [0.35, 0, 0.4], "dims_m": [0.4, 0.4, 0.4]}),
        ],
    )
    out = tier0(app, "fake")
    facts = [f for f in out["facts"] if f["kind"] == "unsupported_com"]
    assert facts, out
    assert "CoM projection" in facts[0]["fix"]


def test_tier0_clean_stack_passes(tmp_path):
    app, _ = _app_with(
        tmp_path,
        [
            ("base", {"location": [0, 0, 0], "dims_m": [0.6, 0.6, 0.4]}),
            ("top", {"location": [0.05, 0, 0.4], "dims_m": [0.4, 0.4, 0.4]}),
        ],
    )
    out = tier0(app, "fake")
    assert out["facts"] == []
    assert "no tier-0 physics conflicts" in out["summary"]


def test_sim_readiness_gate():
    ready = sim_readiness(
        {
            "dimensions": [1, 1, 1],
            "physics_density_kg_m3": 500,
            "collision": "convex",
        }
    )
    assert ready["ready"] is True
    not_ready = sim_readiness({"dimensions": [1, 1, 1]})
    requirements = {f["requirement"] for f in not_ready["findings"]}
    assert {"physical_material", "collision_proxy"} <= requirements
    assert all("fix" in f for f in not_ready["findings"])


# -- tools registration -----------------------------------------------------


def test_physical_tools_register_and_guard(tmp_path):
    from tee.physical.tools import register_physical_tools

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_physical_tools(app, tmp_path)
    names = app.registry.names()
    for expected in (
        "sketch_solve",
        "mat_assign",
        "sim_settle",
        "phys_tier0",
        "plaus_check",
        "wall_with_openings",
        "param_set",
    ):
        assert expected in names
    # tier-2 ops guard non-Blender adapters with the exact fix
    with pytest.raises(TeeError) as err:
        app.registry.call("wall_with_openings", {"props": {}})
    assert err.value.code == "unsupported_adapter"
    # mat_assign works on the fake adapter (assign_material parity)
    created = app.run_batch(
        "fake",
        [{"op": "create", "kind": "cube", "name": "Wall", "props": {"dims_m": [4, 0.2, 2.7]}}],
    )
    out = app.registry.call(
        "mat_assign", {"id": created["created"][0], "query": "concrete", "adapter": "fake"}
    )
    assert out["fact"]["mass_kg"] == pytest.approx(4 * 0.2 * 2.7 * 2400, rel=0.01)


def test_sim_fluid_cost_gate(tmp_path):
    from tee.physical.tools import register_physical_tools

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_physical_tools(app, tmp_path)
    with pytest.raises(TeeError) as err:
        app.registry.call("sim_fluid", {})
    assert err.value.code == "cost_confirmation_required"
    assert "tee_job" in (err.value.fix or "")


def test_fluid_program_caps_resolution():
    from tee.physical.physics import fluid_program

    code = fluid_program([2, 2, 2], [0, 0, 1], resolution=999, cache_dir="/abs/cache")
    assert "resolution_max = 64" in code
    assert '"ALL"' in code
    assert "/abs/cache" in code


def test_ids_data_completeness_tier(tmp_path):
    """IDS 1.0 spec via ifctester against a minimal IFC (both from the
    installed toolchain - skips when the physical extra is absent)."""
    pytest.importorskip("ifctester")
    ifcopenshell_api = pytest.importorskip("ifcopenshell.api")

    model = ifcopenshell_api.run("project.create_file", version="IFC4")
    ifcopenshell_api.run("root.create_entity", model, ifc_class="IfcProject", name="Fixture")
    ifcopenshell_api.run("root.create_entity", model, ifc_class="IfcWall", name="W1")
    ifc_path = tmp_path / "fixture.ifc"
    model.write(str(ifc_path))

    ids_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS"
     xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
     xs:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <info><title>Walls need names</title></info>
  <specifications>
    <specification name="wall-name" ifcVersion="IFC4">
      <applicability minOccurs="0" maxOccurs="unbounded">
        <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
      </applicability>
      <requirements>
        <attribute><name><simpleValue>Name</simpleValue></name></attribute>
      </requirements>
    </specification>
  </specifications>
</ids>
"""
    ids_path = tmp_path / "spec.ids"
    ids_path.write_text(ids_xml)

    from tee.physical.tools import register_physical_tools

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_physical_tools(app, tmp_path)
    out = app.registry.call("plaus_ids", {"ifc": str(ifc_path), "ids": str(ids_path)})
    assert out["specifications"] == 1
    assert "no data-completeness conflicts" in out["summary"], out


# -- masonry family + storey envelope (2026-08-27 gap closure) ---------------


def _wall_model(region="US", **wall):
    base = {
        "id": "w1",
        "class": "wall",
        "thickness_m": 0.22,
        "material": "clay_brick",
        "bearing": True,
        "supports": ["f1"],
    }
    base.update(wall)
    return {"region": region, "elements": [base, {"id": "f1", "class": "footing", "width_m": 0.6}]}


def test_masonry_matches_the_family_not_a_name_whitelist():
    """'clay_brick' and 'concrete_block' walls used to skip the masonry
    checks entirely - a 60 m clay_brick wall sailed through slenderness."""
    for material in ("clay_brick", "concrete_block", "brick_masonry", "stone"):
        out = plaus.check(_wall_model(material=material, height_m=60.0))
        assert any(f["rule"] == "masonry_slenderness" for f in out["findings"]), material
    # cast-in-situ concrete is NOT masonry and must stay out of these checks
    out = plaus.check(_wall_model(material="concrete", height_m=60.0))
    assert not any(f["rule"].startswith("masonry") for f in out["findings"])


def test_storey_envelope_flags_at_heur_and_differs_by_rule_set():
    """3 storeys is inside the IRC's R101.2 scope and beyond the SANS
    empirical envelope; the finding is a scope statement, so HEUR."""
    three = _wall_model(height_m=8.4, stories=3)
    assert not any(
        f["rule"] == "prescriptive_scope_stories" for f in plaus.check(three)["findings"]
    )
    za = plaus.check(_wall_model(region="ZA", height_m=8.4, stories=3))["findings"]
    scope = [f for f in za if f["rule"] == "prescriptive_scope_stories"]
    assert scope and scope[0]["severity"] == "HEUR"
    assert "rational design" in scope[0]["detail"]


def test_storey_envelope_implied_by_wall_height():
    """A tower described only by geometry still trips the envelope: 60 m
    of wall implies ~20 storeys at the 3 m convention."""
    out = plaus.check(_wall_model(region="NA-communal", height_m=60.0))
    scope = [f for f in out["findings"] if f["rule"] == "prescriptive_scope_stories"]
    assert scope and "implies ~20 storeys" in scope[0]["detail"]
    # HEUR sits under every jurisdiction cap, so it is never severity-capped
    assert "severity_capped_from" not in scope[0]


# -- jurisdiction (A29): SANS 10400 / Namibia -------------------------------
#
# The governing fact, from knowledge-base/03_codes_standards/00_overview.md:
# SANS 10400 is law in South Africa (NBR Act 103 of 1977) but NOT in Namibia,
# where it binds only if a council incorporated it under LAA s 94B - and on
# communal land there is no building control at all. So the checker must vary
# both the VALUES it tests against and the FORCE it claims.


def _room(ceiling_m: float, **extra):
    return {
        "elements": [
            {"id": "r1", "class": "room", "ceiling_m": ceiling_m, "habitable": True, **extra}
        ]
    }


def test_us_remains_the_default_and_uses_irc_values():
    """No region, or region=US, must behave exactly as before this existed."""
    bare = plaus.check(_room(2.2))
    explicit = plaus.check({**_room(2.2), "region": "US"})
    assert bare["findings"] == explicit["findings"] == []
    assert bare["jurisdiction"]["region"] == "US"
    assert bare["jurisdiction"]["rule_set"] == "irc"


def test_a_ceiling_legal_under_irc_is_a_finding_under_sans():
    """2,2 m clears the IRC's 2134 mm and fails SANS 10400-C's 2,4 m. The
    jurisdictions genuinely disagree - which is why region has to be real."""
    assert plaus.check({**_room(2.2), "region": "US"})["findings"] == []
    za = plaus.check({**_room(2.2), "region": "ZA"})["findings"]
    assert len(za) == 1
    assert za[0]["rule"] == "ceiling_min_mm"
    assert "2400" in za[0]["detail"]
    assert "SANS 10400-C" in za[0]["source"]


def test_south_africa_may_claim_code_force():
    finding = plaus.check({**_room(2.2), "region": "ZA"})["findings"][0]
    assert finding["severity"] == "CODE"
    assert "severity_capped_from" not in finding


def test_communal_land_caps_code_to_standard_of_care_and_says_why():
    """On communal land no code has been adopted, so the same conflict is a
    professional-standard finding, not a legal one - and the downgrade is
    stated rather than silent."""
    out = plaus.check({**_room(2.2), "region": "NA-communal"})
    finding = out["findings"][0]
    assert finding["severity"] == "STD"
    assert finding["severity_capped_from"] == "CODE"
    assert out["jurisdiction"]["capped_findings"] == 1
    # The reason is stated once for the response, not repeated per finding:
    # the duplicate strings cost 2.5x the payload and said nothing new.
    assert "no building control" in out["jurisdiction"]["legal_basis"].lower()
    assert "severity_cap_reason" not in finding


def test_the_ceiling_binds_every_finding_producer_not_just_hit():
    """load_path and wet-wall findings are built directly rather than through
    hit(). Capping only inside hit() let a response say `max_severity: STD`
    in its header and then emit a CODE finding underneath it."""
    broken = {
        "region": "NA-communal",
        "elements": [
            {"id": "beam", "class": "beam", "span_m": 4.0, "depth_mm": 300, "material": "concrete"},
            {"id": "pad", "class": "footing", "width_m": 0.6, "soil_bearing_kpa": 120},
        ],
    }
    out = plaus.check(broken)
    load_path = [f for f in out["findings"] if f["rule"] == "load_path"]
    assert load_path, "the broken load path should be found at all"
    assert load_path[0]["severity"] == "STD"
    assert load_path[0]["severity_capped_from"] == "CODE"
    ceiling = out["jurisdiction"]["max_severity"]
    order = ("CONV", "HEUR", "STD", "CODE")
    for finding in out["findings"]:
        assert order.index(finding["severity"]) <= order.index(ceiling), finding


def test_bare_namibia_refuses_to_guess_the_regime():
    """'Namibia' alone is not an answer: the three regimes differ completely,
    and assuming one is the documented failure mode."""
    for spelling in ("NA", "namibia"):
        out = plaus.check({**_room(2.2), "region": spelling})
        assert out["jurisdiction"]["region"] == "NA-unresolved"
        assert out["findings"][0]["severity"] == "HEUR"
        assert "Okongo" in out["jurisdiction"]["advisory"]


def test_local_authority_flags_the_s94b_incorporation_question():
    out = plaus.check({**_room(2.2), "region": "NA-local-authority"})
    assert out["jurisdiction"]["max_severity"] == "STD"
    assert "94B" in out["jurisdiction"]["advisory"]


def test_unknown_region_fails_loud_rather_than_defaulting_to_irc():
    with pytest.raises(TeeError) as err:
        plaus.check({**_room(2.2), "region": "Ruritania"})
    assert err.value.code == "unknown_region"
    assert "NA-communal" in (err.value.fix or "")


def test_sans_only_rules_are_absent_from_the_irc_table():
    """A room too small under SANS 10400-C must not be reported under the IRC
    table, which encodes no such rule - inventing one would be a false claim."""
    small = {
        "elements": [
            {
                "id": "r1",
                "class": "room",
                "ceiling_m": 3.0,
                "habitable": True,
                "area_m2": 4.0,
                "min_dimension_m": 1.5,
            }
        ]
    }
    assert plaus.check({**small, "region": "US"})["findings"] == []
    za = plaus.check({**small, "region": "ZA"})["findings"]
    rules_hit = {f["rule"] for f in za}
    assert rules_hit == {"sans_room_min_area"}
    assert len(za) == 2  # area and narrowest dimension are separate findings


def test_sans_stair_geometry_differs_from_irc_in_both_directions():
    """SANS allows a taller riser (200 vs 196) but demands a tighter 2R+G band
    (570-650 vs 550-700). Neither code is uniformly stricter."""
    stair = {
        "elements": [
            {
                "id": "s1",
                "class": "stair",
                "riser_mm": 198,
                "tread_mm": 260,
                "headroom_mm": 2100,
                "width_mm": 800,
            }
        ]
    }
    us = {f["detail"] for f in plaus.check({**stair, "region": "US"})["findings"]}
    za = {f["detail"] for f in plaus.check({**stair, "region": "ZA"})["findings"]}
    assert any("riser 198" in d for d in us)  # over the IRC's 196
    assert not any("riser 198" in d for d in za)  # within the SANS 200
    assert any("width" in d for d in us)  # under the IRC's 914
    assert not any("width" in d for d in za)  # over the SANS 750
    assert any("2R+G" in d for d in za)  # 656 is outside 570-650
    assert not any("2R+G" in d for d in us)  # but inside 550-700


def test_sans_flags_riser_variation_within_a_flight():
    stair = {
        "elements": [
            {
                "id": "s1",
                "class": "stair",
                "riser_mm": 180,
                "tread_mm": 260,
                "headroom_mm": 2100,
                "width_mm": 800,
                "riser_variation_mm": 11,
            }
        ]
    }
    za = plaus.check({**stair, "region": "ZA"})["findings"]
    assert any(f["rule"] == "sans_stair_riser_variation" for f in za)
    # The IRC table encodes no riser-variation rule, so it must not fire there.
    # (It does flag the 800 mm width, which clears SANS's 750 but not IRC's 914 -
    # the codes disagreeing again, which is the point.)
    us = plaus.check({**stair, "region": "US"})["findings"]
    assert not any(f["rule"] == "sans_stair_riser_variation" for f in us)
    assert {f["rule"] for f in us} == {"stairs"}


def test_every_jurisdiction_states_its_legal_basis():
    """A finding without its legal basis invites the reader to assume force it
    does not have."""
    for region in ("US", "ZA", "NA-local-authority", "NA-settlement", "NA-communal"):
        j = plaus.check({**_room(2.5), "region": region})["jurisdiction"]
        assert j["legal_basis"]
        assert j["max_severity"] in ("CODE", "STD", "HEUR", "CONV")


def test_findings_never_become_approvals_in_any_jurisdiction():
    """A20's contract survives the jurisdiction work."""
    for region in ("US", "ZA", "NA-communal"):
        out = plaus.check({**_room(2.5), "region": region})
        # a clean run reports rules evaluated; it never reports a pass
        assert "no plausibility conflicts detected" in out["summary"]
        assert "passes" not in out["summary"].lower()
        assert "compliant" not in out["summary"].lower()
        # and the disclaimer keeps saying absence of findings is not approval
        assert "not an approval" in out["disclaimer"]
