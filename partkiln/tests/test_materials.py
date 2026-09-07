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
