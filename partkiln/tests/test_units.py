"""P1 acceptance for the unit boundary (A66 D4 / Law 12)."""

from __future__ import annotations

import math

import pytest

from partkiln.document import CommandError
from partkiln.units import (
    UnitError,
    canonical_unit,
    format_mm,
    has_unit,
    is_literal,
    parse_angle,
    parse_length,
)


def test_unit_error_is_command_error() -> None:
    assert UnitError is CommandError


@pytest.mark.parametrize(
    ("text", "mm"),
    [
        ("0.5in", 12.7),
        ("3/8in", 9.525),
        ("12mm", 12.0),
        ("1.2cm", 12.0),
        ("0.012m", 12.0),
        ("1ft", 304.8),
        ("10mil", 0.254),
        ("2 inch", 50.8),
        ('1"', 25.4),
        ("-5mm", -5.0),
        (" 7.5 mm ", 7.5),
    ],
)
def test_parse_length_suffixes(text: str, mm: float) -> None:
    assert parse_length(text) == pytest.approx(mm, abs=1e-12)


def test_bare_number_is_the_default_unit() -> None:
    assert parse_length(12) == 12.0
    assert parse_length("12") == 12.0
    assert parse_length(12, default="in") == pytest.approx(304.8)
    assert not has_unit("12")
    assert has_unit("12mm")


def test_unknown_suffix_refuses_naming_accepted_ones() -> None:
    with pytest.raises(UnitError) as excinfo:
        parse_length("12 furlongs")
    message = str(excinfo.value)
    assert "furlongs" in message
    for unit in ("mm", "cm", "m", "in", "ft", "mil"):
        assert unit in message
    assert excinfo.value.code == "pk_unit_unknown"


def test_wrong_kind_refuses_naming_the_kind() -> None:
    with pytest.raises(UnitError) as excinfo:
        parse_angle("90mm")
    assert "length, not an angle" in str(excinfo.value)
    assert excinfo.value.code == "pk_unit_kind"
    with pytest.raises(UnitError) as excinfo:
        parse_length("90deg")
    assert "angle, not a length" in str(excinfo.value)


def test_parse_angle() -> None:
    assert parse_angle("90deg") == 90.0
    assert parse_angle("1.5rad") == pytest.approx(math.degrees(1.5))
    assert parse_angle("45°") == 45.0
    assert parse_angle(30) == 30.0
    assert parse_angle(1, default="rad") == pytest.approx(math.degrees(1))


def test_strict_refuses_bare_numbers_with_the_fix() -> None:
    with pytest.raises(UnitError) as excinfo:
        parse_length(12, default=None)
    assert "12mm" in str(excinfo.value)
    assert "strict_units" in str(excinfo.value)
    assert excinfo.value.code == "pk_unitless"


def test_not_a_number_refuses() -> None:
    with pytest.raises(UnitError):
        parse_length("wide")
    with pytest.raises(UnitError):
        parse_length("1 1/2in")  # one number, one slash
    with pytest.raises(UnitError):
        parse_length("3/0in")
    with pytest.raises(UnitError):
        parse_length(True)  # type: ignore[arg-type]


def test_is_literal_routes_expressions_elsewhere() -> None:
    assert is_literal("12mm")
    assert is_literal("3/8in")
    assert is_literal("12 furlongs")  # a literal with a bad unit is still a unit problem
    assert not is_literal("W/2 - 5mm")
    assert not is_literal("W")


def test_canonical_unit() -> None:
    assert canonical_unit("inch") == "in"
    assert canonical_unit("degrees", "angle") == "deg"
    with pytest.raises(UnitError, match="Accepted length units"):
        canonical_unit("furlong")


def test_format_mm() -> None:
    assert format_mm(12.0) == "12 mm"
    assert format_mm(9.525) == "9.525 mm"
    assert format_mm(0.0254) == "0.0254 mm"
