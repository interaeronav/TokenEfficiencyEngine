"""`standards.fit` shipped with the ISO 286 lane and had no door onto it.

Found by the A66 verify pass: `partkiln/standards.py` derives ISO 286 fits and
`create hole {fit: "H7"}` uses them, but the `standards` method's `what` only
accepted clearance/tap/drill/pitch/fastener/list - so a model driving partkiln
could not ask for a fit at all, could not discover which classes are served,
and could not use the `supplied` escape hatch. The lane was reachable only
from Python. This pins the two `what` values that open it.

Zero always-loaded tools are added: `standards` is an existing method.
"""

from __future__ import annotations

import pytest

from partkiln.client import LocalKernel
from partkiln.document import CommandError


def _call(params: dict[str, object]) -> dict:
    result = LocalKernel().call("standards", params)
    assert isinstance(result, dict)
    return result


def test_the_standards_method_serves_a_derived_fit() -> None:
    """20H7/g6, the textbook running fit. Every micrometre below is ISO 286-1's
    own arithmetic: IT7 at 18-30 mm is 21 um, IT6 is 13, and g's fundamental
    deviation is -2.5 * D**0.34 = -7 um at D = sqrt(18*30)."""
    out = _call({"what": "fit", "designation": "20H7/g6"})
    assert out["what"] == "fit"
    assert out["basis"] == "derived"
    assert out["kind"] == "clearance"
    assert (out["hole"]["min_mm"], out["hole"]["max_mm"]) == (20.0, 20.021)
    assert (out["shaft"]["min_mm"], out["shaft"]["max_mm"]) == (19.98, 19.993)
    assert out["licence"] == "own"


def test_the_standards_method_lists_what_it_will_and_will_not_derive() -> None:
    out = _call({"what": "fits"})
    assert out["what"] == "fits"
    assert set(out) >= {"grades", "positions", "refused", "size_range_mm", "authority"}


def test_a_fit_with_no_designation_names_the_field_and_an_example() -> None:
    with pytest.raises(CommandError) as excinfo:
        _call({"what": "fit"})
    assert "designation" in str(excinfo.value)


def test_a_tabulated_position_refuses_through_the_verb_and_takes_a_supplied_value() -> None:
    """`p` is IT plus a tabulated increment: no formula exists, so it refuses -
    and the same call with the caller's own licensed number is served, marked
    `supplied` so nobody mistakes it for partkiln's arithmetic."""
    with pytest.raises(CommandError) as excinfo:
        _call({"what": "fit", "designation": "20H7/p6"})
    assert excinfo.value.code == "pk_not_served"

    out = _call({"what": "fit", "designation": "20H7/p6", "supplied": {"p6": {"fd_um": 22}}})
    assert out["kind"] == "interference"
    assert (out["shaft"]["min_mm"], out["shaft"]["max_mm"]) == (20.022, 20.035)
    assert out["basis"] == "supplied"


def test_an_unknown_what_still_names_every_option_including_the_two_new_ones() -> None:
    with pytest.raises(CommandError) as excinfo:
        _call({"what": "nope"})
    message = str(excinfo.value)
    assert "fit" in message and "fits" in message
