"""Units at the boundary: everything inside the kernel is millimetres and degrees.

Law 12 of the A66 script: a bare number IS millimetres (or degrees), and the
diff says so once. The document owns that "once"; this module only converts.
A string carries its unit (`"12mm"`, `"0.5in"`, `"3/8in"`, `"90deg"`,
`"1.5rad"`), a number is in the caller's default unit, and the two ways a
string can be wrong each get their own refusal: a suffix of the wrong KIND
(`"90mm"` where an angle was asked for) is named as a kind mismatch, and a
suffix nobody knows (`"12 furlongs"`) is refused with the accepted list -
because "invalid unit" tells a model nothing it can act on.

Fractions are accepted because drills, taps and imperial stock are catalogued
that way (`"3/8in"`, `"1 1/2in"` is NOT - one number, one slash).
"""

from __future__ import annotations

import math
import re

from partkiln.document import CommandError

# The one place a factor lives. 1 mil = 0.001 in = 0.0254 mm (PCB and sheet
# gauge tables); 1 ft = 304.8 mm exactly since the 1959 international yard.
LENGTH_TO_MM: dict[str, float] = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "ft": 304.8,
    "mil": 0.0254,
}
ANGLE_TO_DEG: dict[str, float] = {
    "deg": 1.0,
    "rad": 180.0 / math.pi,
}

# Spellings a person or a datasheet uses; canonicalised before lookup.
_ALIASES: dict[str, str] = {
    "millimeter": "mm",
    "millimeters": "mm",
    "millimetre": "mm",
    "millimetres": "mm",
    "centimeter": "cm",
    "centimeters": "cm",
    "centimetre": "cm",
    "centimetres": "cm",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "inch": "in",
    "inches": "in",
    '"': "in",
    "feet": "ft",
    "foot": "ft",
    "'": "ft",
    "mils": "mil",
    "thou": "mil",
    "degree": "deg",
    "degrees": "deg",
    "°": "deg",
    "radian": "rad",
    "radians": "rad",
}

LENGTH_UNITS: tuple[str, ...] = tuple(LENGTH_TO_MM)
ANGLE_UNITS: tuple[str, ...] = tuple(ANGLE_TO_DEG)

UnitError = CommandError

# sign, number, optional "/denominator", optional suffix.
_LITERAL = re.compile(
    r"^\s*([-+]?)\s*(\d+(?:\.\d*)?|\.\d+)(?:\s*/\s*(\d+(?:\.\d*)?))?\s*([A-Za-z°\"']*)\s*$"
)


def is_literal(text: str) -> bool:
    """True when `text` is a number with an optional unit suffix.

    The document uses this to route a string: a literal goes through
    `parse_length`/`parse_angle` (so `"12 furlongs"` is refused as a UNIT
    problem, with the accepted suffixes), anything else is a parameter
    expression and goes to `partkiln.params`.
    """
    return _LITERAL.match(text) is not None


def has_unit(text: str) -> bool:
    """True when a literal carries a suffix. The document asks this to know
    whether a value was bare - and so whether Law 12's `assumed` is owed."""
    match = _LITERAL.match(text)
    return match is not None and bool(match.group(4))


def _split(text: str, kind: str) -> tuple[float, str]:
    """(magnitude, canonical suffix or '') of a literal, or a refusal."""
    match = _LITERAL.match(text)
    if match is None:
        raise UnitError(
            f"{text!r} is not a {kind}. Write a number with a unit, e.g. "
            f"{'12mm, 0.5in or 3/8in' if kind == 'length' else '90deg or 1.5rad'}.",
            code="pk_unit_unknown",
        )
    sign, numerator, denominator, suffix = match.groups()
    magnitude = float(numerator)
    if denominator:
        if float(denominator) == 0.0:
            raise UnitError(f"{text!r} divides by zero.", code="pk_unit_unknown")
        magnitude /= float(denominator)
    if sign == "-":
        magnitude = -magnitude
    unit = _ALIASES.get(suffix, suffix)
    return magnitude, unit


def _refuse_unknown(text: str, unit: str, kind: str) -> UnitError:
    accepted = LENGTH_UNITS if kind == "length" else ANGLE_UNITS
    return UnitError(
        f"unknown unit {unit!r} in {text!r}. Accepted {kind} units: {', '.join(accepted)}.",
        code="pk_unit_unknown",
    )


def parse_length(value: float | str, default: str | None = "mm") -> float:
    """A length in millimetres.

    `default` is the unit a bare number is in - the document's unit. Pass
    `None` to refuse bare numbers, which is what `strict_units` means.
    """
    if isinstance(value, bool):
        raise UnitError(f"{value!r} is not a length.", code="pk_unit_unknown")
    if isinstance(value, int | float):
        return _bare(float(value), default, "length")
    magnitude, unit = _split(str(value), "length")
    if not unit:
        return _bare(magnitude, default, "length")
    if unit in LENGTH_TO_MM:
        return magnitude * LENGTH_TO_MM[unit]
    if unit in ANGLE_TO_DEG:
        raise UnitError(
            f"{value!r} is an angle, not a length. Write it in "
            f"{', '.join(LENGTH_UNITS)} (e.g. {magnitude:g}mm).",
            code="pk_unit_kind",
        )
    raise _refuse_unknown(str(value), unit, "length")


def parse_angle(value: float | str, default: str | None = "deg") -> float:
    """An angle in degrees. Same contract as `parse_length`."""
    if isinstance(value, bool):
        raise UnitError(f"{value!r} is not an angle.", code="pk_unit_unknown")
    if isinstance(value, int | float):
        return _bare(float(value), default, "angle")
    magnitude, unit = _split(str(value), "angle")
    if not unit:
        return _bare(magnitude, default, "angle")
    if unit in ANGLE_TO_DEG:
        return magnitude * ANGLE_TO_DEG[unit]
    if unit in LENGTH_TO_MM:
        raise UnitError(
            f"{value!r} is a length, not an angle. Write it in "
            f"{', '.join(ANGLE_UNITS)} (e.g. {magnitude:g}deg).",
            code="pk_unit_kind",
        )
    raise _refuse_unknown(str(value), unit, "angle")


def _bare(magnitude: float, default: str | None, kind: str) -> float:
    if default is None:
        example = f"{magnitude:g}mm" if kind == "length" else f"{magnitude:g}deg"
        raise UnitError(
            f"{magnitude:g} has no unit and strict_units is on. Write {example}, "
            "or set doc strict_units=false.",
            code="pk_unitless",
        )
    table = LENGTH_TO_MM if kind == "length" else ANGLE_TO_DEG
    unit = _ALIASES.get(default, default)
    if unit not in table:
        raise _refuse_unknown(f"{magnitude:g}", default, kind)
    return magnitude * table[unit]


def canonical_unit(unit: str, kind: str = "length") -> str:
    """The table spelling of a unit, or a refusal naming the accepted ones."""
    table = LENGTH_TO_MM if kind == "length" else ANGLE_TO_DEG
    name = _ALIASES.get(unit, unit)
    if name not in table:
        raise _refuse_unknown(unit, unit, kind)
    return name


def format_mm(x: float) -> str:
    """Millimetres for a message: `12 mm`, `9.525 mm`, `0.0254 mm`."""
    return f"{x:.6g} mm"


def format_deg(x: float) -> str:
    return f"{x:.6g} deg"
