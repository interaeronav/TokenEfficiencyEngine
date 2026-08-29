"""joinery_check (A37 P5.3): the seeded-defect wardrobe is caught with
cited fixes; the clean fixture reports zero findings with the rule
count; missing model data answers not_evaluated, never a silent pass."""

from __future__ import annotations

from tee.physical.joinery import RULES, check

CLEAN_WARDROBE = {
    "cabinets": [
        {"id": "Wardrobe", "kind": "tall", "width_mm": 1200, "height_mm": 2200, "depth_mm": 600}
    ],
    "parts": [
        {
            "id": "Side",
            "cabinet": "Wardrobe",
            "role": "side",
            "length_mm": 2200,
            "width_mm": 600,
            "thickness_mm": 19,
        },
        {
            "id": "Door",
            "cabinet": "Wardrobe",
            "role": "door",
            "length_mm": 2100,
            "width_mm": 595,
            "thickness_mm": 19,
        },
    ],
    "hardware": [
        {
            "id": "h1",
            "kind": "hinge",
            "cabinet": "Wardrobe",
            "door": "Door",
            "cup_diameter_mm": 35,
            "cup_depth_mm": 12.8,
            "at_mm": [21.5, 100],
        },
        {
            "id": "h2",
            "kind": "hinge",
            "cabinet": "Wardrobe",
            "door": "Door",
            "cup_diameter_mm": 35,
            "cup_depth_mm": 12.8,
            "at_mm": [21.5, 2000],
        },
        {
            "id": "r1",
            "kind": "runner",
            "cabinet": "Wardrobe",
            "nominal_length_mm": 550,
            "load_class_kg": 40,
        },
    ],
    "system_holes": [
        {
            "cabinet": "Wardrobe",
            "row_setback_mm": 37,
            "pitch_mm": 32,
            "diameter_mm": 5,
            "depths_mm": 13,
        }
    ],
}

SEEDED_DEFECTS = {
    "cabinets": [
        {
            "id": "Wardrobe",
            "kind": "tall",
            "width_mm": 1200,
            "height_mm": 2200,
            "depth_mm": 500,
        }  # shallow: hanging warn AND runner misfit
    ],
    "parts": [
        {
            "id": "Shelf",
            "cabinet": "Wardrobe",
            "role": "shelf",
            "length_mm": 994,
            "width_mm": 994,
            "thickness_mm": 19,
        },  # the live HB-5.2 defect class
        {
            "id": "Door",
            "cabinet": "Wardrobe",
            "role": "door",
            "length_mm": 2100,
            "width_mm": 595,
            "thickness_mm": 15,
        },
    ],
    "hardware": [
        {
            "id": "h1",
            "kind": "hinge",
            "cabinet": "Wardrobe",
            "door": "Door",
            "cup_diameter_mm": 26,
            "cup_depth_mm": 12.8,
            "at_mm": [21.5, 100],
        },
        {
            "id": "h2",
            "kind": "hinge",
            "cabinet": "Wardrobe",
            "door": "Door",
            "cup_diameter_mm": 35,
            "cup_depth_mm": 12.8,
            "at_mm": [21.5, 120],
        },
        {
            "id": "r1",
            "kind": "runner",
            "cabinet": "Wardrobe",
            "nominal_length_mm": 650,
            "load_class_kg": 40,
        },
    ],
    "system_holes": [
        {
            "cabinet": "Wardrobe",
            "row_setback_mm": 50,
            "pitch_mm": 25,
            "diameter_mm": 5,
            "depths_mm": 13,
        }  # wrong system holes
    ],
}


def test_clean_wardrobe_reports_zero_findings_with_rule_count() -> None:
    out = check(CLEAN_WARDROBE)
    assert out["ok"] is True
    assert out["findings"] == []
    assert out["not_evaluated"] == []
    assert out["rules_total"] == len(RULES) == 7
    assert out["rules_evaluated"] == 7


def test_seeded_defects_are_each_caught_with_cited_fixes() -> None:
    out = check(SEEDED_DEFECTS)
    assert out["ok"] is False
    rules_hit = {f["rule"] for f in out["findings"]}
    assert {
        "system_pitch",
        "system_setback",
        "hinge_cup",
        "hinge_collision",
        "carcass_runner",
        "part_envelope",
        "wardrobe_depth",
    } <= rules_hit
    for finding in out["findings"]:
        assert finding["fix"], finding["rule"]  # every finding names the fix
        assert finding["source"], finding["rule"]  # and its citation
        assert "2026-08-29" in finding["verified"]  # and the A30 re-check state
    # the wrong-holes seed produced both pitch and setback findings
    pitch = next(f for f in out["findings"] if f["rule"] == "system_pitch")
    assert "25.0" in pitch["finding"]
    # the runner seed violated BOTH the carcass fit and the class range
    runner_findings = [f for f in out["findings"] if f["rule"] == "carcass_runner"]
    assert len(runner_findings) == 2
    # thin door + standard cup = break-through risk, alongside the Ø26 cup
    cup_findings = [f for f in out["findings"] if f["rule"] == "hinge_cup"]
    assert any("break-through" in f["finding"] for f in cup_findings)
    assert any("Ø26" in f["finding"] for f in cup_findings)


def test_missing_hole_data_is_not_evaluated_never_passed() -> None:
    spec = {k: v for k, v in CLEAN_WARDROBE.items() if k != "system_holes"}
    out = check(spec)
    assert out["ok"] is True  # no findings - but the gap is visible:
    skipped = {n["rule"] for n in out["not_evaluated"]}
    assert skipped == {"system_pitch", "system_setback"}
    assert out["rules_evaluated"] == out["rules_total"] - 2
    assert all("not judged, not passed" in n["why"] for n in out["not_evaluated"])


def test_joinery_check_registered_as_virtual_tool(tmp_path) -> None:
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.physical.tools import register_physical_tools

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        register_physical_tools(app, tmp_path)
        out = app.registry.call("joinery_check", {"spec": CLEAN_WARDROBE})
        assert out["ok"] is True and out["rules_total"] == 7
        described = app.registry.describe("joinery_check")
        assert "not_evaluated" in described["description"]
    finally:
        app.shutdown()
