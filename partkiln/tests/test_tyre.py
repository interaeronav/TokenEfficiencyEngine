"""The tyre structure module: the data book's relationships, and no table.

The claim under test is a licence posture as much as an arithmetic one. The
dimension and load tables in an aircraft tyre data book are reprinted with
permission from The Tire and Rim Association, so this lane implements what the
book states as a RELATIONSHIP, quotes what it states as a DEFINITION, and ships
nothing that only a copyrighted table could give - the same posture
`data/iso286.json` takes to ISO 286. Two assertions here guard that directly:
no tyre table is importable from this lane, and asking for one refuses with the
fix ("read your own row").

The arithmetic assertions are anchored on the ONE thing the book prints that
lets you check the formula without copying a table: the formula itself. Given a
mean diameter, a flange diameter and a static loaded radius, `d` is determined,
and every worked figure here is that inversion run forwards and backwards.
"""

from __future__ import annotations

import math

import pytest

from partkiln import tyre
from partkiln.document import CommandError

# The Three-Part size the data book's DEFINITIONS section uses as its worked
# example of size nomenclature - "49x19.0-20: nominal diameter 49 in, nominal
# section width 19.0 in, nominal wheel/rim diameter 20 in". Quoted from the
# definitions, NOT from a load table. Everything else below is a caller's
# number, which is exactly the contract: the module never supplies these.
DEFINITIONS_SIZE = {
    "units": "in",
    "outside_diameter": 49,
    "section_width": 19.0,
    "rim_diameter": 20,
}
# A caller's own row: flange height, tabled SLR, rated load and inflation.
CALLER_ROW = {
    "flange_height": 1.3,
    "static_loaded_radius": 20.5,
    "rated_load": 46000,
    "rated_inflation": 195,
}


def worked() -> dict:
    return tyre.analyse({**DEFINITIONS_SIZE, **CALLER_ROW})


# -- the relationships ---------------------------------------------------------


def test_slr_formula_round_trips_through_percent_deflection() -> None:
    """The book states SLR in terms of d; d recovered from SLR must give SLR
    back. This is the whole basis for refusing to default d: the caller's own
    tabled SLR determines it, so no number has to be invented."""
    mean_d, flange_d = 1244.6, 574.0
    for pct in (0.30, 0.325, 0.35, 0.363):
        slr = tyre.static_loaded_radius_mm(mean_d, flange_d, pct)
        assert tyre.percent_deflection_from_slr(mean_d, flange_d, slr) == pytest.approx(pct)


def test_the_two_percentages_have_different_denominators() -> None:
    """The book's `d` divides by (D_M - D_F)/2 and section height divides by
    H = (D_o - D)/2. Serving one under the other's name is a confident wrong
    answer of several points, so the answer names both and warns."""
    out = worked()
    book = out["percent_deflection"]["percent"]
    of_h = out["percent_of_section_height"]["percent"]
    assert book != pytest.approx(of_h)
    assert book > of_h  # the flange reference is the shorter length
    assert out["percent_deflection"]["referenced_to"].startswith("(D_M - D_F)/2")
    assert "NOT the data book's percent deflection" in out["percent_of_section_height"]["warning"]


def test_section_height_is_the_books_own_formula() -> None:
    """H = (D_o - D)/2, referenced to the rim LEDGE diameter."""
    assert tyre.section_height_mm(49 * 25.4, 20 * 25.4) == pytest.approx(14.5 * 25.4)
    out = worked()
    assert out["section_height"]["in"] == pytest.approx(14.5)
    assert out["section_height"]["formula"] == "H = (D_o - D)/2"


def test_aspect_ratio_matches_the_definition() -> None:
    """ "The ratio of tire section height to tire section width." 14.5/19.0."""
    out = worked()
    assert out["aspect_ratio"]["value"] == pytest.approx(14.5 / 19.0, abs=5e-4)


def test_gyradius_is_unit_free() -> None:
    """(Max O.D. + Min O.D.)/5.12 is a ratio of lengths, so it holds in either
    system - which is why it can be served in both."""
    assert tyre.gyradius_mm(49 * 25.4, 48 * 25.4) / 25.4 == pytest.approx((49 + 48) / 5.12)


def test_outside_diameter_from_circumference() -> None:
    assert tyre.outside_diameter_from_circumference_mm(math.pi * 1244.6) == pytest.approx(1244.6)


# -- deflection, radius, clearance ---------------------------------------------


def test_the_worked_example_end_to_end() -> None:
    """Deflection, loaded radius and clearance for the definitions-section size
    with a caller's row. 24.5 in free radius, 20.5 in loaded -> 4.0 in."""
    out = worked()
    assert out["free_radius"]["in"] == pytest.approx(24.5)
    assert out["deflection"]["in"] == pytest.approx(4.0)
    assert out["deflection"]["mm"] == pytest.approx(101.6)
    assert out["static_loaded_radius"]["in"] == pytest.approx(20.5)
    assert out["percent_deflection"]["percent"] == pytest.approx(30.3, abs=0.05)
    ground = out["ground_clearance"]
    assert ground["axle_height_under_load"]["in"] == pytest.approx(20.5)
    assert ground["drop_from_unloaded"]["in"] == pytest.approx(4.0)


def test_flat_tire_radius_gives_the_bottomed_clearance() -> None:
    """The bottomed case is what a fairing has to survive, and the book defines
    it: the radius "when subjected to bottoming load"."""
    out = tyre.analyse({**DEFINITIONS_SIZE, **CALLER_ROW, "flat_tire_radius": 16.0})
    ground = out["ground_clearance"]
    assert ground["axle_height_bottomed"]["in"] == pytest.approx(16.0)
    assert ground["further_drop_when_bottomed"]["in"] == pytest.approx(4.5)
    assert "bottoming load" in ground["bottomed_definition"]


def test_mean_diameter_says_which_columns_it_used() -> None:
    """D_M is the mean of the OD max and min columns when both are given and
    the max column alone when only one is - a ~2% difference that is ~15% of
    the deflection, so the answer says which."""
    one = worked()
    both = tyre.analyse({**DEFINITIONS_SIZE, **CALLER_ROW, "outside_diameter_min": 48})
    assert one["inputs"]["mean_overall_diameter_from"] == "the OD max column"
    assert both["inputs"]["mean_overall_diameter_from"] == "mean of the OD max and min columns"
    assert both["inputs"]["mean_overall_diameter"]["in"] == pytest.approx(48.5)
    assert both["deflection"]["in"] < one["deflection"]["in"]
    assert "gyradius" in both and "gyradius" not in one


# -- stiffness and patch --------------------------------------------------------


def test_vertical_rate_is_a_secant_and_says_where_it_was_taken() -> None:
    """46 000 lbf over 4.0 in = 11 500 lbf/in. A tyre's curve is not straight,
    so the rate is only valid at the load and pressure it carries with it."""
    out = worked()
    rate = out["vertical_rate"]
    assert rate["lbf_per_in"] == pytest.approx(11500.0, rel=1e-4)
    assert rate["N_per_mm"] == pytest.approx(46000 * tyre.LBF_N / 101.6, rel=1e-3)
    assert "secant" in rate["kind"]
    assert rate["at_load"]["lbf"] == pytest.approx(46000.0)
    assert rate["at_pressure"]["psi"] == pytest.approx(195.0)


def test_vertical_rate_refuses_zero_deflection() -> None:
    with pytest.raises(CommandError) as excinfo:
        tyre.vertical_rate_n_per_mm(1000.0, 0.0)
    assert excinfo.value.code == "pk_needs"
    assert "static_loaded_radius" in str(excinfo.value)


def test_the_contact_patch_is_never_a_bare_number() -> None:
    """A = F/p credits the inflation gas with the whole load; the carcass
    carries part of it, so the true patch is SMALLER. The key is named
    `area_upper_bound_mm2` so even a caller reading one key gets the claim."""
    patch = tyre.contact_patch(1000.0, 1.0)
    assert patch["area_upper_bound_mm2"] == pytest.approx(1000.0)
    assert "area_mm2" not in patch and "area" not in patch
    assert patch["claim"] == "UPPER BOUND, not the patch"
    assert "SMALLER" in patch["why"]
    assert patch["to_do_better"]
    # and through the whole answer, every time
    served = worked()["contact_patch"]
    assert "area_mm2" not in served
    assert served["claim"] == "UPPER BOUND, not the patch"
    assert served["area_upper_bound_in2"] == pytest.approx(46000.0 / 195.0, rel=1e-3)


def test_the_patch_refuses_without_a_pressure() -> None:
    """No p, no F/p - and it says so in place rather than omitting the key."""
    out = tyre.analyse(
        {**DEFINITIONS_SIZE, "flange_height": 1.3, "static_loaded_radius": 20.5, "load": 46000}
    )
    assert out["contact_patch"]["refused"] == "no inflation pressure"
    assert "rated_inflation=" in out["contact_patch"]["why"]
    with pytest.raises(CommandError) as excinfo:
        tyre.contact_patch(1000.0, 0.0)
    assert excinfo.value.code == "pk_needs"


# -- load at a non-rated inflation ----------------------------------------------


def test_derating_below_rated_is_proportional_and_cited() -> None:
    """The one relationship the book states: "For loads less than the maximum,
    the inflation pressure can be reduced proportionately."."""
    load, why = tyre.load_at_inflation_n(1000.0, 2.0, 1.0)
    assert load == pytest.approx(500.0)
    assert "proportionately" in why


def test_above_rated_inflation_refuses_rather_than_extrapolating() -> None:
    """The book states no relationship above rated inflation for a standard
    aircraft tyre, so this refuses and names the exact fix."""
    with pytest.raises(CommandError) as excinfo:
        tyre.load_at_inflation_n(1000.0, 2.0, 2.4)
    assert excinfo.value.code == "pk_not_served"
    message = str(excinfo.value)
    assert "rated_load=" in message and "helicopter" in message
    assert "1.20x rated" in message or "1.20x" in message


def test_helicopter_service_opens_the_one_stated_exception() -> None:
    """ "standard aircraft tires may be rated up to a factor of 1.50 for both
    load and inflation" - to 1.50 and not past it."""
    load, why = tyre.load_at_inflation_n(1000.0, 2.0, 3.0, service="helicopter")
    assert load == pytest.approx(1500.0)
    assert "1.50" in why
    with pytest.raises(CommandError) as excinfo:
        tyre.load_at_inflation_n(1000.0, 2.0, 3.2, service="helicopter")
    assert excinfo.value.code == "pk_not_served"


def test_an_unknown_service_refuses_with_the_two_that_exist() -> None:
    with pytest.raises(CommandError) as excinfo:
        tyre.load_at_inflation_n(1000.0, 2.0, 1.0, service="rally")
    assert excinfo.value.code == "pk_bad_op"
    assert "helicopter" in str(excinfo.value)


def test_a_derated_load_flows_into_the_whole_answer() -> None:
    out = tyre.analyse({**DEFINITIONS_SIZE, **CALLER_ROW, "inflation": 97.5})
    assert out["load"]["lbf"] == pytest.approx(23000.0)
    assert "proportional derating" in out["load"]["basis"]
    assert out["inflation"]["psi"] == pytest.approx(97.5)


# -- units ----------------------------------------------------------------------


def test_both_systems_give_the_same_structure() -> None:
    """The book is inches, pounds and psi; the kernel is mm and N. A row read
    in either must land on the same tyre."""
    imperial = worked()
    metric = tyre.analyse(
        {
            "units": "mm",
            "outside_diameter": 49 * 25.4,
            "section_width": 19.0 * 25.4,
            "rim_diameter": 20 * 25.4,
            "flange_height": 1.3 * 25.4,
            "static_loaded_radius": 20.5 * 25.4,
            "rated_load": 46000 * tyre.LBF_N,
            "rated_inflation": 195 * tyre.PSI_MPA,
        }
    )
    assert metric["deflection"]["mm"] == pytest.approx(imperial["deflection"]["mm"])
    assert metric["percent_deflection"]["percent"] == pytest.approx(
        imperial["percent_deflection"]["percent"]
    )
    assert metric["vertical_rate"]["N_per_mm"] == pytest.approx(
        imperial["vertical_rate"]["N_per_mm"], rel=1e-6
    )


def test_a_suffixed_string_overrides_the_system() -> None:
    """A caller who writes the unit gets the unit they wrote, either way."""
    out = tyre.analyse(
        {
            "units": "mm",
            "outside_diameter": "49in",
            "rim_diameter": "20in",
            "flange_height": "1.3in",
            "static_loaded_radius": "20.5in",
            "rated_load": "46000lbf",
            "rated_inflation": "195psi",
        }
    )
    assert out["deflection"]["in"] == pytest.approx(4.0)
    assert out["load"]["lbf"] == pytest.approx(46000.0)


def test_every_length_carries_both_systems() -> None:
    out = worked()
    for key in ("free_radius", "deflection", "static_loaded_radius"):
        assert set(out[key]) >= {"mm", "in"}
    assert set(out["load"]) >= {"N", "lbf"}
    assert set(out["inflation"]) >= {"MPa", "psi"}


def test_the_conversion_factors_are_the_defined_ones() -> None:
    """1 lbf = 0.45359237 kg x 9.80665 m/s2; 1 psi = 1 lbf / (25.4 mm)2."""
    assert pytest.approx(4.4482216152605, rel=1e-12) == tyre.LBF_N
    assert pytest.approx(0.0068947572931683, rel=1e-12) == tyre.PSI_MPA


def test_an_unknown_unit_names_the_accepted_ones() -> None:
    with pytest.raises(CommandError) as excinfo:
        tyre.analyse({**DEFINITIONS_SIZE, "outside_diameter": "49 furlongs"})
    assert excinfo.value.code == "pk_unit_unknown"
    assert "in" in str(excinfo.value)
    with pytest.raises(CommandError) as excinfo:
        tyre.analyse({**DEFINITIONS_SIZE, "units": "cubits"})
    assert excinfo.value.code == "pk_unit_unknown"


def test_a_uniform_unit_slip_is_invisible_to_ratios_so_the_answer_echoes() -> None:
    """MEASURED, and it drives the design: read every length in inches and pass
    it bare (so every one is taken as mm) and the percentages come out
    bit-identical - they all scale together. There is nothing to detect without
    inventing a threshold for how big a tyre may be. What protects the caller is
    the echo: the system bare numbers were read in, and every length in both."""
    slipped = tyre.analyse(
        {
            "outside_diameter": 49,
            "rim_diameter": 20,
            "flange_height": 1.3,
            "static_loaded_radius": 20.5,
        }
    )
    correct = tyre.analyse(
        {
            "units": "in",
            "outside_diameter": 49,
            "rim_diameter": 20,
            "flange_height": 1.3,
            "static_loaded_radius": 20.5,
        }
    )
    assert slipped["percent_deflection"]["percent"] == correct["percent_deflection"]["percent"], (
        "a uniform slip changed a ratio - then it would be detectable and should be caught"
    )
    assert slipped["deflection"]["mm"] == pytest.approx(4.0)
    assert correct["deflection"]["mm"] == pytest.approx(101.6)
    assert slipped["units"]["bare_numbers_are"]["length"] == "mm"
    assert correct["units"]["bare_numbers_are"]["length"] == "in"


def test_a_mixed_unit_slip_is_caught() -> None:
    """Inconsistent units DO break the geometry, and that refusal names the fix."""
    with pytest.raises(CommandError) as excinfo:
        tyre.analyse(
            {
                "outside_diameter": 49,
                "rim_diameter": "20in",
                "flange_height": 1.3,
                "static_loaded_radius": 20.5,
            }
        )
    assert excinfo.value.code == "pk_needs"
    assert "units='in'" in str(excinfo.value)


# -- what it will not do --------------------------------------------------------


def test_nothing_defaults_the_percent_deflection() -> None:
    """The whole honesty of this module in one assertion. The book states the
    SLR formula in terms of d and never prints d's value - it says only that an
    "H" before the diameter marks a tyre designed for a HIGHER percent
    deflection, naming neither number. So a default would be invented."""
    with pytest.raises(CommandError) as excinfo:
        tyre.analyse({**DEFINITIONS_SIZE, "flange_height": 1.3})
    assert excinfo.value.code == "pk_needs"
    message = str(excinfo.value)
    assert "static_loaded_radius=" in message and "percent_deflection=" in message
    assert "never prints" in message


def test_the_flange_diameter_is_required_not_assumed() -> None:
    """The book's d is referenced to the flange, so guessing the flange would
    silently move every percentage in the answer."""
    with pytest.raises(CommandError) as excinfo:
        tyre.analyse({**DEFINITIONS_SIZE, "static_loaded_radius": 20.5})
    assert excinfo.value.code == "pk_needs"
    assert "flange_height=" in str(excinfo.value)


@pytest.mark.parametrize(
    ("asked", "must_say"),
    [
        ("grip", "not of the tyre alone"),
        ("friction", "not of the tyre alone"),
        ("mu", "not of the tyre alone"),
        ("wear", "measured on a rig"),
        ("wear_rate", "measured on a rig"),
        ("rolling_resistance", "hysteresis"),
        ("crr", "hysteresis"),
        ("temperature", "duty cycle"),
        ("compound", "trade secrets"),
    ],
)
def test_the_unknowable_quantities_refuse_by_name_with_a_fix(asked: str, must_say: str) -> None:
    """Each refusal names its reason AND the fix, exactly as an anisotropic
    material card refuses a scalar it will not invent."""
    with pytest.raises(CommandError) as excinfo:
        tyre.refuse(asked)
    assert excinfo.value.code == "pk_not_served"
    message = str(excinfo.value)
    assert must_say in message
    assert "Fix:" in message


def test_f1_grip_refusal_names_what_pirelli_actually_publishes() -> None:
    """A compound designation is not a compound property, and the refusal has
    to say so or the next reader supplies one from memory."""
    entry = tyre.refusal("grip")
    assert entry is not None
    assert "C1 hardest to C5 softest" in entry["reason"]
    assert "no compound properties whatever" in entry["reason"]


def test_the_tyre_table_itself_is_refused_for_the_licence_reason() -> None:
    """The T&RA refusal is the reason this module exists in this shape."""
    with pytest.raises(CommandError) as excinfo:
        tyre.refuse("rated_load")
    message = str(excinfo.value)
    assert "Tire and Rim Association" in message
    assert "iso286" in message
    assert "read the row" in message


def test_the_clearance_allowance_table_is_refused_too() -> None:
    with pytest.raises(CommandError) as excinfo:
        tyre.refuse("clearance")
    assert "Tire and Rim Association" in str(excinfo.value)
    assert "flat_tire_radius=" in str(excinfo.value)


def test_an_unrefused_quantity_lists_what_is_refused_and_served() -> None:
    with pytest.raises(CommandError) as excinfo:
        tyre.refuse("colour")
    assert excinfo.value.code == "pk_ref_unknown"
    assert "grip" in str(excinfo.value) and "vertical rate" in str(excinfo.value)


def test_every_refusal_carries_a_reason_and_a_fix() -> None:
    """The materials.py invariant, applied here: a refusal with no fix is a
    silence, and a silence gets filled from memory."""
    for name, entry in tyre.REFUSES.items():
        assert entry["reason"].strip(), name
        assert entry["fix"].strip(), name
        assert len(entry["reason"]) > 40 and len(entry["fix"]) > 20, name


# -- the licence posture --------------------------------------------------------


def test_this_lane_ships_no_tyre_table() -> None:
    """The assertion behind the whole design: no data file of real tyres, and
    no dict of them in the module either."""
    from importlib import resources

    names = [p.name for p in resources.files("partkiln.data").iterdir()]
    assert not any("tyre" in n.lower() or "tire" in n.lower() for n in names), names
    # and nothing in the module is a table of tyres keyed by size
    for value in vars(tyre).values():
        if isinstance(value, dict):
            assert not any(
                isinstance(k, str) and ("x" in k and "-" in k and k[0].isdigit()) for k in value
            ), "a size-keyed table appeared in partkiln.tyre"


def test_the_answer_carries_its_attribution_and_citations() -> None:
    out = worked()
    assert "Goodyear Aviation Data Book 2022" in out["citations"]["source"]
    assert "Tire and Rim Association" in out["citations"]["attribution"]
    assert "METHOD OF CALCULATION" in out["percent_deflection"]["cite"]


def test_describe_is_the_discoverable_entry() -> None:
    """A caller learns the inputs before guessing them - and learns, up front,
    that no table ships and what is refused."""
    doc = tyre.describe()
    assert "static_loaded_radius" in doc["needs"]
    assert "Tire and Rim Association" in doc["ships_no_table"]
    assert set(doc["refuses"]) == set(tyre.REFUSES)
    assert "slr" in doc["relationships"] and "derate" in doc["relationships"]
    for definition in doc["definitions"].values():
        assert definition.endswith(".")


def test_the_definitions_are_the_books_own_words() -> None:
    """Quoted, short, with attribution - definitions are what make the inputs
    unambiguous, and they are the one thing quotable from the book."""
    assert tyre.DEFINITIONS["rated_load"] == "The maximum load rating in pounds."
    assert "center of the axle" in tyre.DEFINITIONS["static_loaded_radius"]
    assert "bottom the tire on the rim" in tyre.DEFINITIONS["max_bottoming_load"]
    assert "Tire and Rim Association" in tyre.DEFINITIONS_ATTRIBUTION


def test_the_module_imports_nothing_heavy() -> None:
    """Pure: no OCP, no numpy, no Qt. A FRESH interpreter, because `sys.modules`
    in this one is already dirty from the rest of the suite - asserting against
    it here would pass or fail on test order, which is not evidence."""
    import subprocess
    import sys
    from pathlib import Path

    code = (
        "import sys, partkiln.tyre;"
        "assert 'OCP' not in sys.modules, 'the tyre module imported OCP';"
        "assert 'numpy' not in sys.modules, 'the tyre module imported numpy';"
        "assert 'PySide6' not in sys.modules, 'the tyre module imported Qt';"
        "print('clean')"
    )
    root = str(Path(__file__).resolve().parents[1] / "src")
    done = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": root, "PATH": "/usr/bin:/bin"},
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert "clean" in done.stdout
