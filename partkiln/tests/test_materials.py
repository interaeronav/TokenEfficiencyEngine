"""CFRP and the anisotropy rules: what a material card may and may not invent.

The rest of the material lane is covered in test_methods.py (the `pk_materials`
verb) and test_standards.py (name resolution). This module holds the cards
whose properties depend on DIRECTION, because that is where a scalar is a lie.
"""

from __future__ import annotations

import pytest

from partkiln import materials
from partkiln.data import DataError
from partkiln.document import CommandError

# --------------------------------------------------------------- CFRP: anisotropy


def test_cfrp_serves_a_density_because_that_is_what_mass_uses() -> None:
    """Density is the one material fact the kernel USES, and it is direction-free.

    Derived by rule of mixtures at the datasheet's own basis (60% fibre volume,
    T300 at 1760 kg/m3), with the cured-epoxy density 1150-1300 the only soft
    input - so the served range is that assumption's whole span, not a guess
    dressed as a measurement.
    """
    d = materials.describe("cfrp_t300_ud")
    assert d["values"]["density"] == 1546
    assert d["honesty"]["density"] == "derived"
    assert d["ranges"]["density"] == [1516, 1576]

    # the arithmetic really is the midpoint of the stated assumption
    def mix(rho_matrix: float) -> float:
        return 0.60 * 1760 + 0.40 * rho_matrix

    assert mix(1150) == pytest.approx(1516)
    assert mix(1300) == pytest.approx(1576)
    assert (mix(1150) + mix(1300)) / 2 == pytest.approx(1546)
    assert materials.mass_g("cfrp_t300_ud", 1_000_000) == 1546.0


def test_cfrp_refuses_a_scalar_modulus_and_says_what_to_read() -> None:
    """The failure this guards: a card that merely OMITS E reads as 'not recorded',
    and the next reader supplies one from memory. For a laminate that is wrong by
    an order of magnitude, so the absence is made loud."""
    with pytest.raises(CommandError) as caught:
        materials.property_value("cfrp_t300_ud", "E")
    assert caught.value.code == "pk_needs"
    assert "E_0" in str(caught.value)


def test_cfrp_refuses_yield_with_the_datasheets_own_contradiction() -> None:
    """1820 N/mm2 along the fibres, 76 across them - both printed on the SAME
    datasheet. A single 'yield' would have to be one of them."""
    d = materials.describe("cfrp_t300_ud")
    assert d["values"]["tensile_0"] == 1820
    assert d["values"]["tensile_90"] == 76
    assert d["values"]["tensile_0"] / d["values"]["tensile_90"] > 20
    with pytest.raises(CommandError, match="factor of 24"):
        materials.property_value("cfrp_t300_ud", "yield")


def test_a_family_name_never_silently_means_one_layup() -> None:
    """'cfrp' is a family. UD is the least representative layup for a real part,
    so resolving to it silently would answer a question nobody asked."""
    with pytest.raises(CommandError) as caught:
        materials.resolve("cfrp")
    assert caught.value.code == "pk_ref_ambiguous"
    assert "cfrp_t300_ud" in str(caught.value)


def test_an_anisotropic_card_must_declare_what_it_refuses() -> None:
    """The load-time guard: omitting `refuses` on an anisotropic card is the
    silent failure, so it is a DataError, not a shrug."""
    bad = {
        "family": "x",
        "anisotropic": True,
        "properties": {
            "density": {"value": 1, "unit": "kg/m3", "source": "s", "honesty": "derived"}
        },
    }
    with pytest.raises(DataError, match="lists no `refuses`"):
        materials._validate_anisotropy("bad", bad)
    bad["refuses"] = {"E": {"reason": "r"}}
    with pytest.raises(DataError, match="has no 'fix'"):
        materials._validate_anisotropy("bad", bad)
    bad["refuses"] = {"density": {"reason": "r", "fix": "f"}}
    with pytest.raises(DataError, match="both serves and refuses"):
        materials._validate_anisotropy("bad", bad)


def test_every_isotropic_card_still_answers_a_plain_modulus() -> None:
    """The new refusal must not leak onto the metals."""
    assert materials.property_value("steel_s275", "E") == 210000
    assert materials.property_value("aluminium_6061", "E") > 0
    assert materials.describe("steel_s275")["anisotropic"] is False


# ------------------------------------------------- CFRP: woven, and quasi-isotropic


def test_woven_is_balanced_and_that_is_not_the_same_as_isotropic() -> None:
    """68 GPa along the warp and 66 along the fill - within 3%, which is exactly
    the trap. Rotate the load 45 deg and a plain weave is far softer, and the
    datasheet prints no 45 deg value, so a plain `E` is still refused."""
    d = materials.describe("cfrp_as4_8552_woven")
    assert d["values"]["E_0"] == 68000
    assert d["values"]["E_90"] == 66000
    assert abs(d["values"]["E_0"] - d["values"]["E_90"]) / d["values"]["E_0"] < 0.05
    assert d["honesty"]["density"] == "datasheet"  # PRINTED, not derived
    assert d["values"]["density"] == 1570
    with pytest.raises(CommandError, match="45"):
        materials.property_value("cfrp_as4_8552_woven", "E")


def test_quasi_isotropic_is_the_one_cfrp_card_that_may_serve_a_plain_modulus() -> None:
    """A quasi-isotropic stack really is isotropic IN-PLANE - that is the point
    of the layup - so E and nu are honest scalars here where they are lies on
    the UD and woven cards."""
    d = materials.describe("cfrp_as4_8552_qi")
    assert d["anisotropic"] is False
    assert materials.property_value("cfrp_as4_8552_qi", "E") == pytest.approx(55454, abs=1)
    assert materials.property_value("cfrp_as4_8552_qi", "nu") == pytest.approx(0.298, abs=0.001)
    assert d["honesty"]["E"] == "derived"


def test_the_qi_modulus_barely_moves_over_the_constants_the_datasheet_omits() -> None:
    """Why a derived QI card is honest at all.

    Hexcel prints E1 and E2 but neither G12 nor nu12. Sweeping G12 over a
    FACTOR OF TWO and nu12 over 0.25-0.35 moves the answer 3.5%, because a
    quasi-isotropic laminate's in-plane stiffness is governed by E1 and E2.
    The served range is that whole sweep, so the assumption is visible rather
    than hidden.
    """

    def qi(E1: float, E2: float, G12: float, nu12: float) -> float:
        nu21 = nu12 * E2 / E1
        den = 1 - nu12 * nu21
        q11, q22, q12, q66 = E1 / den, E2 / den, nu12 * E2 / den, G12
        u1 = (3 * q11 + 3 * q22 + 2 * q12 + 4 * q66) / 8
        u4 = (q11 + q22 + 6 * q12 - 4 * q66) / 8
        return (u1 * u1 - u4 * u4) / u1

    swept = [qi(141000, 10000, g, n) for g in (4000, 8500) for n in (0.25, 0.35)]
    lo, hi = min(swept), max(swept)
    assert (hi - lo) / ((hi + lo) / 2) < 0.08  # a factor of two in G12 buys 3.5%
    served = materials.describe("cfrp_as4_8552_qi")
    assert served["ranges"]["E"] == [round(lo), round(hi)]
    assert served["values"]["E"] == pytest.approx((round(lo) + round(hi)) / 2, abs=1)


def test_quasi_isotropic_still_refuses_strength_and_says_why() -> None:
    """Stiffness is quasi-isotropic; strength is not. It turns on which ply
    fails first, so it depends on the stacking sequence this card does not fix."""
    with pytest.raises(CommandError, match="stacking sequence"):
        materials.property_value("cfrp_as4_8552_qi", "yield")


def test_density_is_layup_independent_so_qi_carries_the_printed_ud_value() -> None:
    """Stacking changes stiffness, not mass. The QI card takes the UD laminate
    density Hexcel prints rather than deriving a second, differing number."""
    assert materials.describe("cfrp_as4_8552_qi")["values"]["density"] == 1580
    assert materials.describe("cfrp_as4_8552_qi")["honesty"]["density"] == "datasheet"


def test_an_isotropic_card_may_refuse_and_the_refusal_is_still_validated() -> None:
    """The QI card is not anisotropic yet declares refusals; those must be
    checked too, or a malformed one would slip through unvalidated."""
    bad = {
        "family": "x",
        "anisotropic": False,
        "properties": {
            "density": {"value": 1, "unit": "kg/m3", "source": "s", "honesty": "derived"}
        },
        "refuses": {"E": {"reason": "r"}},
    }
    with pytest.raises(DataError, match="has no 'fix'"):
        materials._validate_anisotropy("bad", bad)


def test_the_family_now_lists_all_three_layups() -> None:
    with pytest.raises(CommandError) as caught:
        materials.resolve("cfrp")
    message = str(caught.value)
    for key in ("cfrp_t300_ud", "cfrp_as4_8552_woven", "cfrp_as4_8552_qi"):
        assert key in message


# --------------------------------------------------- titanium and glass fibre


def test_titanium_is_an_ordinary_isotropic_card() -> None:
    """Ti-6Al-4V is a metal: one E, one yield, no direction. It is the contrast
    that shows the composite refusals are about the material, not the schema."""
    d = materials.describe("titanium_ti6al4v")
    assert d["anisotropic"] is False
    assert d["refuses"] == {}
    assert materials.property_value("titanium_ti6al4v", "E") == 115000
    assert materials.property_value("titanium_ti6al4v", "yield") == 869
    assert materials.resolve("ti64") == "titanium_ti6al4v"
    assert materials.resolve("grade 5 titanium") == "titanium_ti6al4v"


def test_titanium_conversions_are_the_printed_imperial_values() -> None:
    """Every served number is the datasheet's own, converted here and nowhere
    else: 0.160 lb/in3, 16.7e6 psi, and the AMS 4911 minima 134 and 126 ksi."""
    d = materials.describe("titanium_ti6al4v")
    lb_in3 = 0.45359237 / 1.6387064e-5
    ksi = 6.894757
    assert d["values"]["density"] == round(0.160 * lb_in3)
    assert d["values"]["tensile"] == round(134 * ksi)
    assert d["values"]["yield"] == round(126 * ksi)
    # and it lands where the alloy actually sits: denser than aluminium, well
    # under steel, at roughly 4.43 g/cm3
    assert 4400 < d["values"]["density"] < 4460
    assert d["honesty"]["yield"] == "standard_value"  # a specified minimum
    assert d["honesty"]["density"] == "datasheet"


def test_titanium_strengths_are_minima_and_the_note_says_they_fall_with_thickness() -> None:
    """The same trap steel_s275 carries: a specified minimum is not a typical
    value, and it drops in thicker sections."""
    note = materials.describe("titanium_ti6al4v")["notes"][-1]
    assert "SPECIFIED MINIMA" in note
    assert "0.1874" in note and "130" in note


def test_glass_ud_now_rests_on_a_laminate_datasheet_not_a_fibre_one() -> None:
    """The card used to be built from a Vetrotex FIBRE sheet, so it derived E_0
    and REFUSED E_90 because the inverse rule of mixtures is a known-bad model.
    Gurit's SE 75 laminate sheet measures both, so both are served."""
    d = materials.describe("gfrp_eglass_ud")
    assert d["honesty"]["E_0"] == "datasheet"
    assert d["honesty"]["E_90"] == "datasheet"
    assert d["values"]["E_0"] == 51000
    assert d["values"]["E_90"] == 10700  # measured; formerly refused
    assert "E_90" not in d["refuses"]
    assert materials.property_value("gfrp_eglass_ud", "E_90") == 10700


def test_glass_density_is_derived_from_printed_inputs_only() -> None:
    """Still `derived`, but nothing in it is assumed any more: fibre density,
    cured resin density and fibre volume fraction are all printed."""
    d = materials.describe("gfrp_eglass_ud")
    assert d["honesty"]["density"] == "derived"
    assert d["values"]["density"] == round(0.473 * 2600 + 0.527 * 1190)
    assert "range" not in str(d["ranges"].get("density", ""))  # no assumption span left
    assert d["ranges"].get("density") is None


def test_the_two_fibre_volumes_on_the_glass_card_are_declared() -> None:
    """The starred datasheet values are normalized to 55% Vf while the density
    and the 90 deg values are as measured at 47.3%. Mixing them silently is how
    a specific-stiffness number goes wrong, so the note says so."""
    note = " ".join(materials.describe("gfrp_eglass_ud")["notes"])
    assert "TWO FIBRE VOLUMES" in note
    assert "47.3" in note and "55%" in note


def test_woven_glass_is_the_most_balanced_card_here() -> None:
    d = materials.describe("gfrp_eglass_woven")
    assert d["values"]["E_0"] == d["values"]["E_90"] == 32000
    with pytest.raises(CommandError, match="45"):
        materials.property_value("gfrp_eglass_woven", "E")


def test_a_carbon_ud_card_with_a_measured_transverse_modulus() -> None:
    """cfrp_t300_ud must refuse E_90 - a fibre datasheet cannot supply it. The
    SE 75 card measures it, and the two densities agree to 1.3% by independent
    routes, which is a check on both."""
    measured = materials.describe("cfrp_hec_se75_ud")
    assert measured["values"]["E_90"] == 8700
    assert measured["values"]["E_0"] / measured["values"]["E_90"] > 15
    toray = materials.describe("cfrp_t300_ud")
    assert "E_90" not in toray["values"]
    drift = abs(measured["values"]["density"] - toray["values"]["density"])
    assert drift / toray["values"]["density"] < 0.02


def test_glass_against_carbon_is_not_a_single_comparison() -> None:
    """The comparison a reader wants, from the cards rather than a sentence -
    and it cuts both ways, which is the point. Compared like for like (both
    SE 75 UD, both measured), glass is heavier and far softer ALONG the fibres
    and yet stiffer ACROSS them, because the transverse direction is the
    matrix's job and glass carries more of it."""
    glass = materials.describe("gfrp_eglass_ud")["values"]
    carbon = materials.describe("cfrp_hec_se75_ud")["values"]
    assert glass["density"] > carbon["density"]
    assert glass["E_0"] < carbon["E_0"] / 2
    assert glass["E_90"] > carbon["E_90"]


def test_commercially_pure_titanium_is_a_third_the_strength_at_the_same_weight() -> None:
    """Why the two grades must not share a name: Grade 2 yields at 276 N/mm2
    where Ti-6Al-4V yields at 869, a factor of 3.15, at densities 2% apart."""
    cp = materials.describe("titanium_grade2")["values"]
    alloy = materials.describe("titanium_ti6al4v")["values"]
    assert cp["yield"] == 276
    assert alloy["yield"] / cp["yield"] > 3
    assert abs(cp["density"] - alloy["density"]) / alloy["density"] < 0.03
    # printed here and NOT on the Ti-6Al-4V sheet, so it is served here only
    assert cp["nu"] == 0.32
    assert "nu" not in alloy


def test_grade_2_values_are_the_astm_b265_minima_converted() -> None:
    ksi, lb_in3 = 6.894757, 0.45359237 / 1.6387064e-5
    d = materials.describe("titanium_grade2")
    assert d["values"]["tensile"] == round(50 * ksi)  # B265 minimum 50 ksi
    assert d["values"]["yield"] == round(40 * ksi)  # B265 minimum 40 ksi
    assert d["values"]["density"] == round(0.163 * lb_in3)
    assert d["honesty"]["yield"] == "standard_value"
    assert d["honesty"]["nu"] == "datasheet"


def test_a_bare_titanium_no_longer_silently_means_the_alloy() -> None:
    """It used to resolve to Ti-6Al-4V. With two grades that differ 3.15x in
    yield, a family name must refuse and name them - the cfrp ruling applied
    to a metal."""
    with pytest.raises(CommandError) as caught:
        materials.resolve("titanium")
    assert caught.value.code == "pk_ref_ambiguous"
    assert "titanium_grade2" in str(caught.value)
    assert "titanium_ti6al4v" in str(caught.value)


# ------------------------------------------------------- 7075 and 316


def test_316_is_typical_values_where_the_steels_are_minima() -> None:
    """The honesty tier cuts both ways. steel_s275's ReH is a specified
    MINIMUM; Aperam prints 316L's 300 MPa as a TYPICAL value, and EN 10088-2's
    minimum is materially lower. A design to the standard must not use this."""
    d = materials.describe("stainless_1_4404")
    assert d["values"]["yield"] == 300
    assert d["values"]["tensile"] == 620
    assert d["honesty"]["yield"] == "datasheet"  # NOT standard_value
    assert materials.describe("steel_s275")["honesty"]["yield"] == "standard_value"
    note = " ".join(d["notes"])
    assert "TYPICAL values, not specified minima" in note
    assert "EN 10088-2" in note


def test_316_is_stronger_than_304_and_that_is_not_why_you_pick_it() -> None:
    """The molybdenum is the point: 316 resists chlorides where 304 pits. The
    card says so, because a strength comparison alone would mislead."""
    s316 = materials.describe("stainless_1_4404")
    s304 = materials.describe("stainless_1_4301")
    assert s316["values"]["yield"] > s304["values"]["yield"]
    assert "chlorides" in " ".join(s316["notes"])
    assert s316["values"]["nu"] == 0.30  # printed here, absent on the 304 card


def test_7075_follows_the_self_consistent_half_of_a_contradictory_source() -> None:
    """The datasheet prints 'Yield 24-68 ksi, 455-465 MPa'. 24-68 ksi is
    165-469 MPa, so the two cannot be the same quantity: the ksi range spans
    tempers and the MPa figures are the T6 end. Its tensile line IS consistent,
    which is what makes the T6 reading defensible."""
    ksi = 6.894757
    assert 24 * ksi == pytest.approx(165, abs=1)
    assert 68 * ksi == pytest.approx(469, abs=1)
    assert 40 * ksi == pytest.approx(276, abs=1)  # tensile low end, consistent
    assert 78 * ksi == pytest.approx(538, abs=1)  # tensile high end, consistent
    d = materials.describe("aluminium_7075_t6")
    assert d["values"]["yield"] == 465  # the T6 end, not the span
    assert d["values"]["tensile"] == 540
    assert "CONTRADICTS ITSELF" in " ".join(d["notes"])


def test_7075_is_about_twice_the_yield_of_6061_at_the_same_stiffness() -> None:
    strong = materials.describe("aluminium_7075_t6")["values"]
    common = materials.describe("aluminium_6061")["values"]
    assert strong["yield"] / common["yield"] > 1.8
    assert abs(strong["E"] - common["E"]) / common["E"] < 0.05  # stiffness barely moves
    assert strong["density"] > common["density"]  # and it is slightly heavier


def test_the_metal_families_refuse_now_that_each_has_several_grades() -> None:
    """aluminium spans 240-465 N/mm2 in yield and stainless changes which
    corrosion it survives, so neither bare name may pick silently."""
    for family, members in (
        ("aluminium", ("aluminium_6061", "aluminium_7075_t6")),
        ("stainless", ("stainless_1_4301", "stainless_1_4404")),
    ):
        with pytest.raises(CommandError) as caught:
            materials.resolve(family)
        assert caught.value.code == "pk_ref_ambiguous"
        for member in members:
            assert member in str(caught.value)
    # ... while the specific names still resolve
    assert materials.resolve("316") == "stainless_1_4404"
    assert materials.resolve("304") == "stainless_1_4301"
    assert materials.resolve("7075") == "aluminium_7075_t6"


def test_steel_is_a_family_too_and_mass_was_never_the_risk() -> None:
    """The fifth and last of these, and the most interesting because the danger
    is narrower. Every steel card sits at 7810-7850 kg/m3, so the one thing the
    kernel USES - mass - barely moved whichever the alias picked. It is the
    STRENGTH that differs (210 to 355 N/mm2 in yield), and 100Cr6 is a hardened
    bearing steel that does not belong in the same sentence as structural
    plate. So the word is retired as an alias, not because it was giving wrong
    masses but because it was giving confident yields."""
    with pytest.raises(CommandError) as caught:
        materials.resolve("steel")
    assert caught.value.code == "pk_ref_ambiguous"
    for member in ("steel_s275", "steel_s355", "steel_dc01", "steel_100cr6"):
        assert member in str(caught.value)

    grades = [n for n in materials.names() if n.startswith("steel_")]
    densities = [materials.describe(n)["values"]["density"] for n in grades]
    assert max(densities) - min(densities) <= 40  # mass was never the risk
    yields = [materials.describe(n)["values"].get("yield") for n in grades]
    yields = [y for y in yields if y is not None]
    assert max(yields) / min(yields) > 1.6  # strength always was

    # the specific names, and the W1 bracket's mass, are untouched
    assert materials.resolve("s275") == "steel_s275"
    assert materials.resolve("mild steel") == "steel_s275"
    assert materials.mass_g("steel_s275", 91158.6) == 715.595


# ------------------------------------------------------- PEEK and PA66


def test_peek_is_a_datasheet_card_with_a_test_method_per_row() -> None:
    """The plastics were the weakest-sourced cards in the lane. PEEK arrives
    from Victrex's own sheet, naming the ISO method for every value."""
    d = materials.describe("peek_450g")
    assert d["values"] == {
        "density": 1300,
        "E": 4000,
        "yield": 98,
        "elongation": 25,
        "E_flexural": 3800,
    }
    assert set(d["honesty"].values()) == {"datasheet"}
    assert "ISO 527-1" in d["sources"]["E"]
    assert "ISO 1183" in d["sources"]["density"]


def test_peek_says_its_numbers_are_all_room_temperature() -> None:
    """PEEK is bought for temperature, so a card of 23 C values is exactly the
    thing a reader could misuse. The note says so rather than leaving it."""
    note = " ".join(materials.describe("peek_450g")["notes"])
    assert "EVERY VALUE HERE IS 23 C" in note
    assert "125 C" in note
    assert "CRYSTALLINE" in note  # and which density it is


def test_pa66_carries_the_moisture_caveat_from_the_datasheet_itself() -> None:
    """A polyamide's stiffness falls as it takes up water. PA6 already said so
    from a handbook; PA66 says it from Ensinger's own 'directly after
    machining' wording."""
    d = materials.describe("nylon_pa66")
    assert d["values"]["E"] == 3500
    assert "after machining" in d["sources"]["E"]
    assert "DRY AS MACHINED" in " ".join(d["notes"])


def test_pa66_is_stiffer_than_pa6_which_is_why_nylon_had_to_go() -> None:
    """Sixth family name retired. PA66 is about 30% stiffer than PA6, so a bare
    'nylon' was quietly choosing a stiffness."""
    pa66 = materials.describe("nylon_pa66")["values"]
    pa6 = materials.describe("nylon_pa6")["values"]
    assert pa66["E"] / pa6["E"] > 1.25
    with pytest.raises(CommandError) as caught:
        materials.resolve("nylon")
    assert caught.value.code == "pk_ref_ambiguous"
    assert "nylon_pa6" in str(caught.value) and "nylon_pa66" in str(caught.value)
    assert materials.resolve("pa6") == "nylon_pa6"
    assert materials.resolve("pa66") == "nylon_pa66"


def test_no_bare_family_name_resolves_to_a_member_any_more() -> None:
    """The whole sweep, asserted in one place: every name that once picked a
    member silently now refuses and lists them."""
    for family in ("cfrp", "gfrp", "titanium", "stainless", "aluminium", "steel", "nylon"):
        with pytest.raises(CommandError) as caught:
            materials.resolve(family)
        assert caught.value.code == "pk_ref_ambiguous", family


# ------------------------------------------- printed plastics: the layer is the weak axis


def test_a_printed_part_is_anisotropic_and_the_layer_bond_is_the_number() -> None:
    """The last handbook cards, rebuilt on printed-specimen datasheets - and it
    turned them into anisotropic cards. Prusa measures 51 and 59 N/mm2 for two
    specimen orientations and 17 for the INTERLAYER BOND: a third of the
    in-plane figure, and what a part pulled across its layers actually fails
    at. A single `yield` would have hidden a factor of three."""
    d = materials.describe("pla")
    assert d["anisotropic"] is True
    assert d["values"]["tensile_horizontal"] == 51
    assert d["values"]["interlayer_adhesion"] == 17
    assert d["values"]["tensile_horizontal"] / d["values"]["interlayer_adhesion"] > 2.9
    with pytest.raises(CommandError, match="INTERLAYER BOND"):
        materials.property_value("pla", "yield")


def test_the_printed_modulus_is_well_below_the_bulk_handbook_figure() -> None:
    """Why rebuilding ABS mattered rather than just re-citing it. The card used
    to serve a handbook E of 2200 N/mm2; a manufacturer testing PRINTED
    specimens reports 1500-1650 in plane."""
    d = materials.describe("abs")
    assert d["values"]["E_xy"] == 1575
    assert d["ranges"]["E_xy"] == [1500, 1650]
    assert d["values"]["E_xy"] < 2200 * 0.8
    assert d["honesty"]["E_xy"] == "datasheet"  # a datasheet range, not a handbook spread
    with pytest.raises(CommandError, match=r"\(X-Y\)"):
        materials.property_value("abs", "E")


def test_every_printed_card_still_answers_mass_because_density_is_honest() -> None:
    """Direction ruins strength, not mass. Both cards keep serving a density,
    and both say the solid assumption out loud."""
    for name, rho in (("pla", 1240), ("abs", 1050)):
        assert materials.property_value(name, "density") == rho
        assert materials.mass_g(name, 1_000_000) == float(rho)
        note = " ".join(materials.describe(name)["notes"])
        assert "infill" in note


# The cards still resting on an unnamed engineering handbook rather than a
# named datasheet or standard. Every plastic has now left this list; what
# remains is a known frontier, pinned so it cannot grow quietly.
HANDBOOK_SOURCED = {
    "aluminium_6061",
    "aluminium_6082",
    "brass_cw614n",
    "nylon_pa6",
    "stainless_1_4301",
    "steel_100cr6",
    "steel_dc01",
}


def test_the_handbook_frontier_is_exactly_what_we_think_it_is() -> None:
    """Not a claim that every card is datasheet-sourced - seven are not, and
    pretending otherwise would be the failure this lane exists to prevent.
    This pins WHICH, so the list can only shrink deliberately and can never
    grow by accident."""
    handbook = {
        name
        for name in materials.names()
        for leaf in materials.card(name)["properties"].values()
        if "engineering handbook" in leaf["source"]
    }
    assert handbook == HANDBOOK_SOURCED
    # ... and no printed plastic is among them any more
    assert not handbook & {"pla", "abs", "peek_450g", "nylon_pa66"}
