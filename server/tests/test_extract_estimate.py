"""SI-B22 — estimated dimensions, and the discipline that keeps them honest.

The point of these tests is not the arithmetic, which is one division. It
is that an estimate can never quietly become a measurement: it refuses
without a mitigation, it carries a band that widens when the caller is
vague, and it lands in a field no consumer of measurements will read.
"""

from __future__ import annotations

import math

import pytest

from tee.extract import estimate
from tee.kernel.errors import TeeError

OK = {
    "reference_iso216": "a4",
    "reference_edge": "long",
    "reference_px": 240,
    "target_px": 1310,
    "coplanar": True,
}


# -- the discipline ---------------------------------------------------------


def test_an_estimate_is_never_reported_as_a_measurement():
    """The whole risk in this feature: a number that reads as measured
    later. `mm` is the measured field name used elsewhere in the lane; an
    estimate must not occupy it."""
    r = estimate.estimate_length(OK)
    assert r["estimated"] is True and r["measured"] is False
    assert "estimated_mm" in r
    assert "mm" not in r and "measured_mm" not in r and "length_mm" not in r


def test_no_reference_means_no_estimate():
    """The refusal IS the feature. Without something of known size there is
    nothing to mitigate the guess with."""
    with pytest.raises(TeeError) as e:
        estimate.estimate_length({"reference_px": 240, "target_px": 1310, "coplanar": True})
    assert e.value.code == "estimate_no_reference"
    assert "will not supply the size itself" in e.value.fix


def test_tee_refuses_to_invent_the_reference_size():
    """Asked for a 'standard door', TEE must not answer 2032 mm. Door
    leaves vary by region and era, and a hallucinated reference becomes a
    structural dimension downstream."""
    src = __import__("pathlib").Path(estimate.__file__).read_text()
    for invented in ("door", "brick", "course", "window_height"):
        assert f'"{invented}"' not in src.lower().split("iso_216")[0], (
            f"a built-in size table for '{invented}' is exactly the hazard"
        )
    # The only built-in sizes are an international standard with exact mm.
    assert set(estimate.ISO_216) == {"a0", "a1", "a2", "a3", "a4", "a5", "a6"}
    assert estimate.ISO_216["a4"] == (210, 297)


def test_every_answer_names_its_mitigation_and_its_assumption():
    r = estimate.estimate_length(OK)
    assert "ISO 216 A4" in r["mitigation"]
    assert "ONE plane" in r["assumption"]
    assert "not a measurement" in r["note"]
    assert "governs" in r["note"]  # a drawing outranks this


def test_the_plane_assumption_must_be_affirmed_not_defaulted():
    """A scale off the near wall does not measure the far wall, and no
    arithmetic here can notice. So the caller affirms it."""
    with pytest.raises(TeeError) as e:
        estimate.estimate_length({**OK, "coplanar": False})
    assert e.value.code == "estimate_not_coplanar"
    assert "near wall" in e.value.fix


# -- the band ---------------------------------------------------------------


def test_vagueness_widens_the_band():
    """An unstated tolerance is not a zero tolerance. Saying less must cost
    accuracy, or callers are rewarded for withholding what they know."""
    vague = estimate.estimate_length(
        {"reference_mm": 900, "reference_px": 240, "target_px": 1310, "coplanar": True}
    )
    precise = estimate.estimate_length(
        {
            "reference_mm": 900,
            "reference_tolerance_mm": 1,
            "reference_px": 240,
            "target_px": 1310,
            "coplanar": True,
        }
    )
    assert vague["band_mm"] > precise["band_mm"]
    assert vague["estimated_mm"] == precise["estimated_mm"]  # same value, worse claim


def test_a_reference_too_small_to_carry_a_scale_is_refused():
    with pytest.raises(TeeError) as e:
        estimate.estimate_length({**OK, "reference_px": 12})
    assert e.value.code == "estimate_reference_too_small"


def test_the_band_shrinks_as_the_reference_fills_more_of_the_frame():
    """Physical sense check: pixel-picking error is a fixed number of
    pixels, so a bigger reference is a proportionally better one."""
    small = estimate.estimate_length({**OK, "reference_px": 60, "target_px": 1310})
    large = estimate.estimate_length({**OK, "reference_px": 600, "target_px": 1310})
    assert large["relative_error"] < small["relative_error"]


def test_the_arithmetic_is_the_obvious_one():
    """Compared at the module's own reported precision. It rounds to 0.1 mm
    on purpose - an estimate off a photograph that claims 1621.125 mm is
    lying about how well it knows the answer."""
    r = estimate.estimate_length(OK)
    assert r["estimated_mm"] == round(297 / 240 * 1310, 1)
    assert r["band_mm"] == pytest.approx(r["estimated_mm"] * r["relative_error"], abs=0.1)


def test_errors_combine_in_quadrature_not_by_addition():
    """Independent errors add in quadrature; summing them would overstate
    the band and make every estimate look worse than it is."""
    r = estimate.estimate_length(OK)
    rel_ref = 1.0 / 297
    rel_a = estimate.EDGE_PICK_PX / 240
    rel_b = estimate.EDGE_PICK_PX / 1310
    assert r["relative_error"] == round(math.sqrt(rel_ref**2 + rel_a**2 + rel_b**2), 4)
    # and it must be SMALLER than naive addition, which is the point
    assert r["relative_error"] < rel_ref + rel_a + rel_b


# -- bad input --------------------------------------------------------------


def test_bad_inputs_refuse_with_a_fix():
    with pytest.raises(TeeError):
        estimate.estimate_length({**OK, "reference_iso216": "a9"})
    with pytest.raises(TeeError):
        estimate.estimate_length({**OK, "reference_edge": "diagonal"})
    with pytest.raises(TeeError):
        estimate.estimate_length({**OK, "target_px": -5})
    with pytest.raises(TeeError):
        estimate.estimate_length({"reference_mm": 0, "reference_px": 240,
                                  "target_px": 100, "coplanar": True})  # fmt: skip


def test_the_tool_is_registered_on_the_read_tier():
    """An estimate reads; it changes nothing."""
    import tempfile

    from tee.app import TeeApp
    from tee.extract.tools import register_extract_tools

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    register_extract_tools(app, tempfile.mkdtemp())
    assert app.registry._tools["ex_estimate"].capability == "read-extract"
