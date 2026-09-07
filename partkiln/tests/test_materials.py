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
