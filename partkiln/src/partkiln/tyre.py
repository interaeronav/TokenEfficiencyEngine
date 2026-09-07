"""Tyre STRUCTURE from the caller's rated data: the `pk_tyre` backend.

`materials.py` refuses "tyre", "f1 tyre" and "aircraft tyre" as materials, and
the refusal is right: a tyre is several rubber compounds over textile or steel
cords with belts and a bead, so it has a vertical rate in N/mm that depends on
inflation pressure, not a modulus, and no density that means anything for a
part's mass. This module is the other half of that refusal - the structural
half, which a landing gear, bracket or fairing designer actually needs.

**It ships no tyre table, deliberately.** The dimension and load tables in an
aircraft tyre data book carry "REPRINTED WITH PERMISSION FROM THE TIRE AND RIM
ASSOCIATION"; they are not ours to redistribute. This is the ISO 286 precedent
already in this lane (`data/iso286.json`): what a source publishes as a
RELATIONSHIP may be implemented with a citation, what it publishes only as a
table may not be copied. So the caller passes the rated data they read off the
book they hold, and this module computes structure from it. The definitions
below are quoted - short definitions of terms, with attribution - because they
are what make those inputs unambiguous.

The one number the data book does NOT give is the standard percent deflection.
It states the SLR relationship in terms of `d`, "Percent Tire Deflection (in
decimal form)", and leaves `d` to the reader; the only thing it says about the
value is that an "H" in front of the diameter "identif[ies] a tire that is
designed for a higher percent deflection", naming neither number. So nothing
here defaults `d`. Either the caller states it, or `percent_deflection_from_slr`
recovers it by inverting the book's own formula on the book's own tabled SLR -
which is the honest route, because it uses only numbers the caller already has.

Two ratios are easy to confuse and this module keeps them apart by name. The
book's `d` is referenced to (D_M - D_F)/2, the tyre's height above the rim
FLANGE; its section height is H = (D_o - D)/2, referenced to the rim LEDGE.
They are not the same denominator and they do not give the same percentage.

One measured fact shapes the unit handling. A UNIFORM unit slip - every length
read in inches and passed as a bare number, so every one is taken as
millimetres - is arithmetically invisible: percent deflection, aspect ratio and
every other ratio come out bit-identical, because they all scale together. Only
the magnitudes move. So this module does not pretend to catch it with a
plausibility threshold (that would be inventing a number about how big a tyre
is allowed to be); it states which system it read bare numbers in and returns
every length in BOTH, so a 4 mm deflection on a 49-unit tyre is visible in the
answer itself. A MIXED slip does get caught, by the geometry guards.

No OCP, no document mutation, no numpy - `import partkiln.tyre` costs nothing.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln.document import CommandError
from partkiln.units import LENGTH_TO_MM

# --------------------------------------------------------------------------- source

SOURCE = (
    "Goodyear Aviation Data Book 2022 (The Goodyear Tire & Rubber Company), "
    "Section 3 Definitions and Abbreviations, Section 1 Introduction, and "
    "Section 7 Engineering and Technical Information"
)

# Short definitions of terms, quoted with attribution, because an input whose
# meaning is guessed is worse than no input. The TABLES those terms index are
# T&RA-licensed and are NOT here: the caller reads their own row.
DEFINITIONS: dict[str, str] = {
    "rated_load": "The maximum load rating in pounds.",
    "rated_inflation": "The inflation pressure required for the tire to support the rated load.",
    "static_loaded_radius": (
        "The distance from the center of the axle to the deflected tread surface under "
        "normal load and inflation pressure."
    ),
    "max_bottoming_load": (
        "Approximate load required to bottom the tire on the rim at rated inflation pressure."
    ),
    "flat_tire_radius": (
        "The distance from the center of the axle to the deflected tread surface when "
        "subjected to bottoming load."
    ),
    "aspect_ratio": "The ratio of tire section height to tire section width.",
    "inflated_dimensions": "The dimensions of a new tire inflated to rated inflation pressure.",
    "max_braking_load": "The maximum steady braking load which may be applied to a tire.",
}
DEFINITIONS_ATTRIBUTION = (
    f"Definitions quoted from {SOURCE}, Section 3. The dimension and load TABLES those "
    "terms index are reprinted in that book with permission from The Tire and Rim "
    "Association and are not reproduced here - read your own row and pass it in."
)

# Relationships implemented here, each with the clause it came from. A number
# in this lane that cannot name one of these is a guess.
CITATIONS: dict[str, str] = {
    "slr": (
        "SLR = D_M/2 - d[(D_M - D_F)/2], where D_M = mean overall tire diameter at "
        "centreline, D_F = rim flange outer diameter, d = percent tire deflection in "
        f"decimal form. {SOURCE}, Section 7, 'Aircraft Tire Dimensions and Deflection', "
        "METHOD OF CALCULATION."
    ),
    "section_height": (
        f"H = (D_o - D)/2, where D_o = outside diameter and D = rim ledge diameter. "
        f"{SOURCE}, Section 7, same figure."
    ),
    "aspect_ratio": (f"Aspect Ratio = section height / section width. {SOURCE}, Section 3."),
    "derate": (
        "'Loads shown are the recommended maximum for the indicated inflation. For loads "
        f"less than the maximum, the inflation pressure can be reduced proportionately.' "
        f"{SOURCE}, Section 1."
    ),
    "helicopter": (
        "'When used on helicopters, standard aircraft tires may be rated up to a factor "
        "of 1.50 for both load and inflation. In limited cases, maximum inflation of 1.8 "
        f"times normal inflation may be permissible.' {SOURCE}, Section 7."
    ),
    "gyradius": (
        "Radius of gyration (tire assemblies), approximate = (Max O.D. + Min O.D.)/5.12. "
        f"{SOURCE}, Section 7."
    ),
    "outside_diameter": (
        f"OD = circumference / pi, measured mounted, inflated and stood 12 hours at "
        f"ambient. {SOURCE}, Section 7, 'Tire Measurement Procedure'."
    ),
    "h_prefix": (
        '\'Some sizes have a letter such as "H" in front of the diameter. This is to '
        "identify a tire that is designed for a higher percent deflection.' "
        f"{SOURCE}, Section 3."
    ),
}

# --------------------------------------------------------------------------- units

# The kernel is mm and N; the data book is inches, pounds and psi. Every factor
# below is written with the definition it comes from, so a reader can check it
# rather than trust it.
_IN_MM = LENGTH_TO_MM["in"]  # 25.4 exactly, international yard 1959
# 1 lbf = (0.45359237 kg international pound) x (9.80665 m/s2 standard gravity).
LBF_N = 0.45359237 * 9.80665
# 1 psi = 1 lbf / 1 in2, and 1 in2 = 25.4**2 mm2, so psi -> N/mm2 (= MPa).
PSI_MPA = LBF_N / (_IN_MM * _IN_MM)

SYSTEMS = ("mm", "in")
_SYSTEM_UNITS = {
    "mm": {"length": "mm", "force": "N", "pressure": "MPa"},
    "in": {"length": "in", "force": "lbf", "pressure": "psi"},
}

_LENGTH_SUFFIX = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": _IN_MM, "inch": _IN_MM}
_FORCE_SUFFIX = {"n": 1.0, "kn": 1000.0, "lbf": LBF_N, "lb": LBF_N, "lbs": LBF_N, "kgf": 9.80665}
_PRESSURE_SUFFIX = {
    "mpa": 1.0,
    "n/mm2": 1.0,
    "kpa": 1e-3,
    "pa": 1e-6,
    "bar": 0.1,
    "psi": PSI_MPA,
}


def _split(text: str) -> tuple[float, str]:
    """(magnitude, lowercased suffix) of `13.75in`, `3450 lbf`, `135psi`."""
    body = text.strip().replace('"', "in")
    index = len(body)
    while index > 0 and not (body[index - 1].isdigit() or body[index - 1] == "."):
        index -= 1
    number, suffix = body[:index].strip(), body[index:].strip().lower()
    try:
        return float(number), suffix
    except ValueError as exc:
        raise CommandError(
            f"{text!r} is not a number with a unit. Write e.g. '13.75in', '3450lbf', '135psi'.",
            code="pk_unit_unknown",
        ) from exc


def _measure(value: Any, kind: str, table: dict[str, float], system: str, field: str) -> float:
    """One input in the kernel's unit (mm, N or MPa), or a refusal that names
    the accepted suffixes. A bare number is in `system`'s unit and the answer
    says so - Law 12's `assumed`, applied to a book printed in inches."""
    if isinstance(value, bool) or value is None:
        raise CommandError(
            f"{field} must be a number or a number with a unit, not {value!r}.",
            code="pk_unit_unknown",
        )
    if isinstance(value, int | float):
        return float(value) * table[_SYSTEM_UNITS[system][kind].lower()]
    magnitude, suffix = _split(str(value))
    if not suffix:
        return magnitude * table[_SYSTEM_UNITS[system][kind].lower()]
    if suffix not in table:
        raise CommandError(
            f"unknown {kind} unit {suffix!r} in {field}={value!r}. Accepted: "
            f"{', '.join(sorted(table))}.",
            code="pk_unit_unknown",
        )
    return magnitude * table[suffix]


def _length_mm(value: Any, system: str, field: str) -> float:
    return _measure(value, "length", _LENGTH_SUFFIX, system, field)


def _force_n(value: Any, system: str, field: str) -> float:
    return _measure(value, "force", _FORCE_SUFFIX, system, field)


def _pressure_mpa(value: Any, system: str, field: str) -> float:
    return _measure(value, "pressure", _PRESSURE_SUFFIX, system, field)


def _both_length(mm: float) -> dict[str, float]:
    """Every length on the wire carries both systems: the caller read inches."""
    return {"mm": round(mm, 3), "in": round(mm / _IN_MM, 4)}


def _both_force(newtons: float) -> dict[str, float]:
    return {"N": round(newtons, 1), "lbf": round(newtons / LBF_N, 1)}


def _both_pressure(mpa: float) -> dict[str, float]:
    return {"MPa": round(mpa, 4), "psi": round(mpa / PSI_MPA, 1)}


def _system(units: Any) -> str:
    if units is None:
        return "mm"
    name = str(units).strip().lower()
    if name in ("inch", "inches", "imperial", "us"):
        name = "in"
    if name in ("metric", "si", "millimetre", "millimeter"):
        name = "mm"
    if name not in SYSTEMS:
        raise CommandError(
            f"units={units!r} is not a system. Pass 'mm' (kernel default: bare numbers are "
            "mm, N, MPa) or 'in' (bare numbers are inches, lbf, psi - what the data book "
            "prints). A suffixed string such as '13.75in' overrides either way.",
            code="pk_unit_unknown",
        )
    return name


# --------------------------------------------------------------------------- refusals

# Quantities people reasonably ask a tyre module for that no relationship in a
# data book can give. Each names its reason and the fix, exactly as an
# anisotropic material card refuses a scalar it will not invent
# (`materials.py::_validate_refusals`) - because a silent omission is filled
# from memory by the next reader, and for a tyre that memory is folklore.
REFUSES: dict[str, dict[str, str]] = {
    "grip": {
        "reason": (
            "a friction coefficient is a property of the tyre AND the surface AND the "
            "temperature AND the slip ratio at that instant, not of the tyre alone: the "
            "same tyre gives mu ~0.7 on dry asphalt and ~0.2 on wet, and peaks at a slip "
            "the tyre does not choose. For a Formula 1 tyre it is also unobtainable in "
            "principle - Pirelli publishes the compound DESIGNATIONS (C1 hardest to C5 "
            "softest), their operating temperature windows and the tyre dimensions, and no "
            "compound properties whatever"
        ),
        "fix": (
            "state the mu you are designing to as YOUR assumption, from a measurement on "
            "your surface, and put it in the report as an assumption; this module will "
            "size the structure around whatever load that mu produces"
        ),
    },
    "wear": {
        "reason": (
            "wear rate is a compound-times-surface-times-duty answer measured on a rig or "
            "a track, not a computable property: it moves by an order of magnitude with "
            "abrasive surface texture and with temperature, and no published tyre datum "
            "predicts it"
        ),
        "fix": (
            "take a wear rate from your own test or your supplier's service data for YOUR "
            "surface and duty cycle, and pass the resulting load history in"
        ),
    },
    "rolling_resistance": {
        "reason": (
            "rolling resistance is hysteresis in the carcass and tread over a duty cycle - "
            "it depends on inflation, load, speed and the tyre's running temperature, all "
            "of which change as it rolls - so it is measured (SAE J1269 / ISO 28580 class "
            "procedures), never derived from dimensions and a rated load"
        ),
        "fix": (
            "measure it, or take a coefficient from the tyre maker for your inflation and "
            "load; the vertical structure this module computes is independent of it"
        ),
    },
    "temperature": {
        "reason": (
            "running temperature is the result of the whole duty cycle - speed, load, "
            "inflation, ambient and brake heat soak - and is a test result, not a lookup. "
            "The data book states operating LIMITS, not a running temperature: aircraft "
            "tyres are not recommended where surface temperatures exceed 225 F (107 C), or "
            "where brake heat exceeds 300 F (149 C) at wheel surfaces adjacent to the tyre"
        ),
        "fix": (
            "design to the stated limits (107 C surface, 149 C at the wheel) and get the "
            "running temperature from a test or from the tyre maker"
        ),
    },
    "compound": {
        "reason": (
            "the rubber compounds in a tyre are trade secrets; no maker publishes modulus, "
            "density or filler loading per compound, and a tyre is several of them at once "
            "over cords, so no single set of numbers describes it"
        ),
        "fix": (
            "for the rubber alone see pk_materials (rubber_nbr, rubber_epdm) and say in "
            "your report that it is a generic stand-in, not the tyre's compound"
        ),
    },
    "rated_load": {
        "reason": (
            "rated load, rated inflation and the inflated dimensions come from the tyre "
            "maker's dimension and load tables, which are reprinted with permission from "
            "The Tire and Rim Association. This lane implements the data book's "
            "RELATIONSHIPS and quotes its DEFINITIONS; it deliberately ships no tyre table, "
            "for the same licence reason `data/iso286.json` ships formulae and no tolerance "
            "table"
        ),
        "fix": (
            "read the row for your size out of the data book you hold and pass its numbers "
            "in: rated_load=, rated_inflation=, outside_diameter=, static_loaded_radius="
        ),
    },
    "clearance_allowance": {
        "reason": (
            "the tyre-to-structure growth and minimum clearance allowances are a table from "
            "The Tire and Rim Association (the data book's 'Growth and Minimum Clearance "
            "Allowance - Bias / Radial' pages, reprinted with permission), not a "
            "relationship, so there is nothing to derive them from"
        ),
        "fix": (
            "read the allowance for your size and construction from that table and add it "
            "to the loaded envelope this module returns; `flat_tire_radius=` gives you the "
            "bottomed case, which is the other half of the same clearance question"
        ),
    },
}
_REFUSAL_ALIASES = {
    "friction": "grip",
    "mu": "grip",
    "coefficient_of_friction": "grip",
    "traction": "grip",
    "grip_coefficient": "grip",
    "wear_rate": "wear",
    "tread_wear": "wear",
    "abrasion": "wear",
    "rolling_friction": "rolling_resistance",
    "crr": "rolling_resistance",
    "rolling": "rolling_resistance",
    "running_temperature": "temperature",
    "operating_temperature": "temperature",
    "heat": "temperature",
    "modulus": "compound",
    "density": "compound",
    "material": "compound",
    "rubber": "compound",
    "table": "rated_load",
    "lookup": "rated_load",
    "size": "rated_load",
    "rated_inflation": "rated_load",
    "load_table": "rated_load",
    "clearance": "clearance_allowance",
    "growth": "clearance_allowance",
}


def refusal(quantity: str) -> dict[str, str] | None:
    """The refusal for a quantity name or alias, or None if it is not refused."""
    key = str(quantity).strip().lower().replace(" ", "_").replace("-", "_")
    key = _REFUSAL_ALIASES.get(key, key)
    entry = REFUSES.get(key)
    return {"quantity": key, **entry} if entry is not None else None


def refuse(quantity: str) -> None:
    """Raise the named refusal, or a `pk_ref_unknown` listing what is refused."""
    entry = refusal(quantity)
    if entry is None:
        raise CommandError(
            f"{quantity!r} is not a quantity this module refuses by name. It refuses: "
            f"{', '.join(sorted(REFUSES))}. It computes: deflection, percent deflection, "
            "static loaded radius, ground clearance, vertical rate and contact patch.",
            code="pk_ref_unknown",
        )
    raise CommandError(
        f"{entry['quantity']} is not a property of a tyre this lane can serve: "
        f"{entry['reason']}. Fix: {entry['fix']}.",
        code="pk_not_served",
    )


# --------------------------------------------------------------------------- geometry


def section_height_mm(outside_diameter_mm: float, rim_ledge_diameter_mm: float) -> float:
    """H = (D_o - D)/2, the data book's own section height (CITATIONS['section_height']).

    D is the rim LEDGE diameter, not the flange - which is why H and the book's
    percent deflection do not share a denominator.
    """
    return (outside_diameter_mm - rim_ledge_diameter_mm) / 2.0


def static_loaded_radius_mm(
    mean_diameter_mm: float, flange_diameter_mm: float, percent_deflection: float
) -> float:
    """SLR from the book's METHOD OF CALCULATION (CITATIONS['slr']).

    `percent_deflection` is `d`, in decimal form - 0.33, not 33.
    """
    return mean_diameter_mm / 2.0 - percent_deflection * (
        (mean_diameter_mm - flange_diameter_mm) / 2.0
    )


def percent_deflection_from_slr(
    mean_diameter_mm: float, flange_diameter_mm: float, slr_mm: float
) -> float:
    """`d` recovered by inverting the book's formula on the book's tabled SLR.

    This is the honest route to `d`: the data book states the relationship in
    terms of `d` and never prints its value, so a default here would be
    invented. The caller already holds SLR - it is a column in the same row as
    the rated load - so `d` costs them nothing.
    """
    span = (mean_diameter_mm - flange_diameter_mm) / 2.0
    if span <= 0:
        raise CommandError(
            f"mean overall diameter {mean_diameter_mm:.4g} mm is not larger than the rim "
            f"flange diameter {flange_diameter_mm:.4g} mm, so there is no tyre above the "
            "flange to deflect. Check that outside_diameter and rim_diameter are in the "
            "same units (pass units='in' if you are reading inches off the data book).",
            code="pk_needs",
        )
    return (mean_diameter_mm / 2.0 - slr_mm) / span


def gyradius_mm(od_max_mm: float, od_min_mm: float) -> float:
    """Approximate radius of gyration of the tyre assembly (CITATIONS['gyradius']).

    A ratio of lengths, so the constant 5.12 is unit-free and this works in
    either system. Spin-up drag needs it; it is stated as approximate.
    """
    return (od_max_mm + od_min_mm) / 5.12


def outside_diameter_from_circumference_mm(circumference_mm: float) -> float:
    """OD = circumference / pi (CITATIONS['outside_diameter']).

    The book's measurement procedure: mounted on its proper rim, inflated to
    the tabled pressure, stood at least 12 hours at ambient, pressure checked.
    """
    return circumference_mm / math.pi


# --------------------------------------------------------------------------- structure


def vertical_rate_n_per_mm(load_n: float, deflection_mm: float) -> float:
    """Secant rate: load / deflection at ONE load and ONE pressure.

    A secant, never a tangent: a tyre's load-deflection curve is not straight,
    so this number is only the rate between the origin and the stated point,
    and it moves with inflation pressure. Extrapolating it to another load or
    another pressure is a different number, which is why the answer carries the
    load and pressure it was taken at.
    """
    if deflection_mm <= 0:
        raise CommandError(
            "a vertical rate needs a positive deflection; at zero deflection the tyre is "
            "carrying no load and the rate is undefined. Give static_loaded_radius= (or "
            "percent_deflection=) for the loaded condition you want the rate at.",
            code="pk_needs",
        )
    return load_n / deflection_mm


def contact_patch(load_n: float, pressure_mpa: float) -> dict[str, Any]:
    """The pressure-vessel first approximation A = F/p, as an UPPER BOUND.

    Never a bare number, in any code path. F/p assumes the inflation gas carries
    the whole load; the carcass, bead and belts carry part of it, so the
    pressure only has to act over a smaller area and the true patch is SMALLER
    than F/p. The key is named `area_upper_bound_mm2` rather than `area_mm2`
    precisely so a caller that reads one key off this dict still gets the claim
    right.
    """
    if pressure_mpa <= 0:
        raise CommandError(
            "contact patch needs a positive inflation pressure; at zero pressure the "
            "carcass carries everything and A = F/p is meaningless. Pass "
            "rated_inflation= (psi if units='in').",
            code="pk_needs",
        )
    area_mm2 = load_n / pressure_mpa
    return {
        "area_upper_bound_mm2": round(area_mm2, 1),
        "area_upper_bound_in2": round(area_mm2 / (_IN_MM * _IN_MM), 3),
        "formula": "A = F / p (inflation pressure carries the load)",
        "claim": "UPPER BOUND, not the patch",
        "why": (
            "A = F/p is the pressure-vessel first approximation: it credits the inflation "
            "gas with the whole load. The carcass, belts and bead carry part of it, so the "
            "true contact area is SMALLER than this. Use it as a bound - for bearing "
            "pressure on a surface, or a first pass at a footprint - not as the footprint."
        ),
        "to_do_better": (
            "measure the footprint at your load and pressure (ink or pressure film), or "
            "get the loaded footprint from the tyre maker"
        ),
    }


def load_at_inflation_n(
    rated_load_n: float,
    rated_inflation_mpa: float,
    inflation_mpa: float,
    *,
    service: str = "aircraft",
) -> tuple[float, str]:
    """Load at a non-rated inflation, using the ONLY relationship the book states.

    Section 1: "Loads shown are the recommended maximum for the indicated
    inflation. For loads less than the maximum, the inflation pressure can be
    reduced proportionately." That licenses proportional DERATING - down from
    rated - and nothing else. Above rated inflation the book states no
    relationship for a standard aircraft tyre, so this refuses rather than
    extrapolating; `service='helicopter'` opens the one exception the book does
    state, a factor of up to 1.50 on BOTH load and inflation.

    Returns (load, the sentence that justifies it).
    """
    if rated_inflation_mpa <= 0 or rated_load_n <= 0:
        raise CommandError(
            "rated_load and rated_inflation must both be positive; they are the row you "
            "read out of the data book.",
            code="pk_needs",
        )
    if inflation_mpa <= 0:
        raise CommandError("inflation must be positive.", code="pk_needs")
    ratio = inflation_mpa / rated_inflation_mpa
    mode = str(service).strip().lower()
    if mode not in ("aircraft", "helicopter"):
        raise CommandError(
            f"service={service!r} is not a service. Pass 'aircraft' (proportional derating "
            "below rated inflation) or 'helicopter' (the book's up-to-1.50 factor on both "
            "load and inflation).",
            code="pk_bad_op",
        )
    if ratio <= 1.0:
        return rated_load_n * ratio, (
            "proportional derating below rated inflation, the one relationship the data "
            f"book states: {CITATIONS['derate']}"
        )
    if mode == "helicopter" and ratio <= 1.50:
        return rated_load_n * ratio, (
            "helicopter service: the book permits a factor of up to 1.50 on BOTH load and "
            f"inflation, applied to the standard aircraft tyre rating. {CITATIONS['helicopter']}"
        )
    limit = "1.50x rated (helicopter service)" if mode == "helicopter" else "rated"
    raise CommandError(
        f"an inflation of {inflation_mpa / PSI_MPA:.1f} psi is {ratio:.2f}x rated, above "
        f"{limit}, and the data book states no load relationship there - it says only that "
        "for loads LESS than the maximum the pressure can be reduced proportionately. "
        "Extrapolating above rated inflation would be inventing a number. Fix: read the "
        "rated load for the higher-pressure rating (a different ply rating or LR row) out "
        "of your data book and pass it as rated_load=, or for a helicopter application "
        "pass service='helicopter', which the book rates to 1.50x on both load and "
        "inflation (1.8x inflation in limited cases, by agreement with the maker).",
        code="pk_not_served",
    )


# --------------------------------------------------------------------------- the answer


def _need(params: dict[str, Any], key: str, why: str) -> Any:
    value = params.get(key)
    if value is None:
        raise CommandError(f"{key} is required: {why}", code="pk_needs")
    return value


def analyse(params: dict[str, Any]) -> dict[str, Any]:
    """The structural answer for one tyre, from the caller's rated data.

    Required: `outside_diameter` and `rim_diameter` (the specified rim, i.e. the
    rim LEDGE diameter, as the data book's wheel columns print it). Then one of
    `static_loaded_radius` (the tabled column - preferred, it needs no assumed
    number) or `percent_deflection`. `flange_height` gives the rim flange outer
    diameter D_F = D + 2h; pass `flange_diameter` directly if you have it.
    Optional: `load` (defaults to `rated_load`), `rated_load`, `rated_inflation`,
    `inflation`, `section_width`, `outside_diameter_min`, `flat_tire_radius`.
    """
    system = _system(params.get("units"))
    unit_names = _SYSTEM_UNITS[system]

    od = _length_mm(
        _need(
            params,
            "outside_diameter",
            "the inflated outside diameter from your data book row (use the MAX column, "
            "which is what the book's dimensional figure is drawn to).",
        ),
        system,
        "outside_diameter",
    )
    rim = _length_mm(
        _need(
            params,
            "rim_diameter",
            "the specified rim (ledge) diameter from the wheel columns of your row.",
        ),
        system,
        "rim_diameter",
    )
    if od <= rim:
        raise CommandError(
            f"outside_diameter {od:.4g} mm is not larger than rim_diameter {rim:.4g} mm. "
            "If you are reading inches off the data book, pass units='in' - a bare number "
            "is millimetres here (the kernel's Law 12).",
            code="pk_needs",
        )

    od_min = params.get("outside_diameter_min")
    od_min_mm = _length_mm(od_min, system, "outside_diameter_min") if od_min is not None else None
    # D_M is the book's "mean overall tire diameter @ C/L". With both columns it
    # is their mean; with only the max column it IS the max, and the answer says
    # which, because the two differ by ~2% and that is ~15% of the deflection.
    mean_d = (od + od_min_mm) / 2.0 if od_min_mm is not None else od
    mean_basis = (
        "mean of the OD max and min columns" if od_min_mm is not None else "the OD max column"
    )

    if params.get("flange_diameter") is not None:
        flange_d = _length_mm(params["flange_diameter"], system, "flange_diameter")
        flange_basis = "given"
    elif params.get("flange_height") is not None:
        height = _length_mm(params["flange_height"], system, "flange_height")
        flange_d = rim + 2.0 * height
        flange_basis = "D + 2 x flange_height"
    else:
        raise CommandError(
            "the rim flange outer diameter is required: the data book's percent deflection "
            "is referenced to it, not to the section height. Pass flange_height= (the "
            "'Flange Height' column of your row; D_F = D + 2h) or flange_diameter= "
            "directly.",
            code="pk_needs",
        )

    slr_given = params.get("static_loaded_radius")
    pct_given = params.get("percent_deflection")
    if slr_given is not None:
        slr = _length_mm(slr_given, system, "static_loaded_radius")
        pct = percent_deflection_from_slr(mean_d, flange_d, slr)
        pct_basis = (
            "recovered by inverting the data book's own SLR formula on the tabled static "
            "loaded radius - no assumed number anywhere in it"
        )
    elif pct_given is not None:
        pct = float(pct_given)
        if pct > 1.0:  # a caller who typed 33 meant 33 per cent
            pct = pct / 100.0
        slr = static_loaded_radius_mm(mean_d, flange_d, pct)
        pct_basis = "stated by the caller; SLR computed from the data book's formula"
    else:
        raise CommandError(
            "give static_loaded_radius= (the tabled column - preferred) or "
            "percent_deflection=. The data book states the SLR relationship in terms of "
            "d, 'Percent Tire Deflection (in decimal form)', and never prints d's value: "
            "the only thing it says is that an 'H' before the diameter marks a tyre "
            "'designed for a higher percent deflection'. So nothing here defaults it - a "
            "default would be an invented number in the middle of your landing gear.",
            code="pk_needs",
        )
    if slr <= 0 or slr >= mean_d / 2.0:
        raise CommandError(
            f"a static loaded radius of {slr:.4g} mm is not between zero and the free "
            f"radius {mean_d / 2.0:.4g} mm. Check the units (pass units='in' for a data "
            "book row) and that static_loaded_radius is a RADIUS, not a diameter.",
            code="pk_needs",
        )

    free_radius = mean_d / 2.0
    deflection = free_radius - slr
    height = section_height_mm(od, rim)
    span = (mean_d - flange_d) / 2.0

    out: dict[str, Any] = {
        "what": "tyre_structure",
        "units": {"bare_numbers_are": unit_names, "answers_carry": "both systems"},
        "inputs": {
            "outside_diameter": _both_length(od),
            "rim_ledge_diameter": _both_length(rim),
            "rim_flange_diameter": _both_length(flange_d),
            "flange_diameter_from": flange_basis,
            "mean_overall_diameter": _both_length(mean_d),
            "mean_overall_diameter_from": mean_basis,
        },
        "section_height": {
            **_both_length(height),
            "formula": "H = (D_o - D)/2",
            "cite": CITATIONS["section_height"],
        },
        "free_radius": _both_length(free_radius),
        "deflection": {
            **_both_length(deflection),
            "meaning": "free radius minus static loaded radius, at the stated load",
        },
        "percent_deflection": {
            "percent": round(pct * 100.0, 2),
            "decimal": round(pct, 5),
            "referenced_to": "(D_M - D_F)/2, the tyre's height above the rim FLANGE",
            "reference_length": _both_length(span),
            "basis": pct_basis,
            "cite": CITATIONS["slr"],
        },
        "percent_of_section_height": {
            "percent": round(deflection / height * 100.0, 2),
            "referenced_to": "H = (D_o - D)/2, referenced to the rim LEDGE",
            "warning": (
                "this is NOT the data book's percent deflection: the book's d divides by "
                "(D_M - D_F)/2 and this divides by H, so the two differ by several points "
                "on the same tyre. Quote the one whose denominator you mean."
            ),
        },
        "static_loaded_radius": {
            **_both_length(slr),
            "definition": DEFINITIONS["static_loaded_radius"],
        },
        "ground_clearance": {
            "axle_height_under_load": _both_length(slr),
            "drop_from_unloaded": _both_length(deflection),
            "meaning": (
                "under this load the axle centre sits this far above the ground, so a "
                "bracket or fairing mounted h above the axle clears by SLR + h and one "
                "mounted h below clears by SLR - h."
            ),
        },
        "citations": {"source": SOURCE, "attribution": DEFINITIONS_ATTRIBUTION},
        "notes": [],
    }

    if od_min_mm is not None:
        out["gyradius"] = {
            **_both_length(gyradius_mm(od, od_min_mm)),
            "kind": "approximate radius of gyration, tyre assembly",
            "cite": CITATIONS["gyradius"],
        }

    width = params.get("section_width")
    if width is not None:
        width_mm = _length_mm(width, system, "section_width")
        if width_mm > 0:
            out["aspect_ratio"] = {
                "value": round(height / width_mm, 3),
                "definition": DEFINITIONS["aspect_ratio"],
                "cite": CITATIONS["aspect_ratio"],
            }

    flat = params.get("flat_tire_radius")
    if flat is not None:
        flat_mm = _length_mm(flat, system, "flat_tire_radius")
        out["ground_clearance"]["axle_height_bottomed"] = _both_length(flat_mm)
        out["ground_clearance"]["further_drop_when_bottomed"] = _both_length(slr - flat_mm)
        out["ground_clearance"]["bottomed_definition"] = DEFINITIONS["flat_tire_radius"]
        out["notes"].append(
            "the bottomed case is the clearance a fairing must survive, not the loaded one."
        )

    # -- load-dependent quantities ------------------------------------------
    rated_load = params.get("rated_load")
    rated_inflation = params.get("rated_inflation")
    inflation = params.get("inflation")
    load = params.get("load")

    load_n: float | None = None
    load_basis = ""
    if load is not None:
        load_n = _force_n(load, system, "load")
        load_basis = "stated by the caller"
    elif rated_load is not None:
        rated_n = _force_n(rated_load, system, "rated_load")
        if inflation is not None and rated_inflation is not None:
            load_n, load_basis = load_at_inflation_n(
                rated_n,
                _pressure_mpa(rated_inflation, system, "rated_inflation"),
                _pressure_mpa(inflation, system, "inflation"),
                service=str(params.get("service") or "aircraft"),
            )
        else:
            load_n, load_basis = rated_n, "the rated load, at rated inflation"

    pressure_mpa: float | None = None
    if inflation is not None:
        pressure_mpa = _pressure_mpa(inflation, system, "inflation")
    elif rated_inflation is not None:
        pressure_mpa = _pressure_mpa(rated_inflation, system, "rated_inflation")

    if load_n is not None:
        out["load"] = {**_both_force(load_n), "basis": load_basis}
        if rated_load is not None:
            out["load"]["rated"] = _both_force(_force_n(rated_load, system, "rated_load"))
        out["vertical_rate"] = {
            "N_per_mm": round(vertical_rate_n_per_mm(load_n, deflection), 1),
            "lbf_per_in": round(vertical_rate_n_per_mm(load_n, deflection) / LBF_N * _IN_MM, 1),
            "kind": "secant (load / deflection), not a tangent stiffness",
            "at_load": _both_force(load_n),
            "at_pressure": _both_pressure(pressure_mpa) if pressure_mpa is not None else None,
            "why": (
                "a tyre's load-deflection curve is not straight and it moves with inflation "
                "pressure, so this rate is the secant from the origin to THIS load at THIS "
                "pressure. It is not valid at another load or another pressure."
            ),
        }
        if pressure_mpa is not None:
            out["inflation"] = _both_pressure(pressure_mpa)
            out["contact_patch"] = contact_patch(load_n, pressure_mpa)
        else:
            out["contact_patch"] = {
                "refused": "no inflation pressure",
                "why": (
                    "A = F/p needs p. Pass rated_inflation= (psi if units='in') and the "
                    "patch comes back as an upper bound."
                ),
            }
    else:
        out["notes"].append(
            "no load given, so no vertical rate and no contact patch: pass rated_load= "
            "(and rated_inflation=) from your data book row for those."
        )

    out["refuses"] = {name: entry["reason"] for name, entry in REFUSES.items()}
    return out


def describe() -> dict[str, Any]:
    """What this module serves, what it quotes, and what it refuses - the
    discoverable entry, so a caller learns the inputs before guessing them."""
    return {
        "what": "help",
        "serves": [
            "vertical deflection at load, and percent deflection (two denominators, named)",
            "static loaded radius, and ground clearance under load and bottomed",
            "vertical rate as a secant, N/mm at a stated load and pressure",
            "contact patch as an UPPER BOUND (A = F/p), never a bare area",
            "load at a non-rated inflation, by proportional derating only",
            "section height, aspect ratio, approximate radius of gyration",
        ],
        "needs": (
            "your data book row: outside_diameter, rim_diameter, flange_height, and "
            "static_loaded_radius (preferred) or percent_deflection; rated_load and "
            "rated_inflation for the load-dependent answers"
        ),
        "ships_no_table": (
            "the dimension and load tables are reprinted with permission from The Tire and "
            "Rim Association; this lane implements the relationships and quotes the "
            "definitions, as `data/iso286.json` does for ISO 286"
        ),
        "definitions": dict(DEFINITIONS),
        "attribution": DEFINITIONS_ATTRIBUTION,
        "relationships": dict(CITATIONS),
        "refuses": {name: dict(entry) for name, entry in REFUSES.items()},
        "units": (
            "bare numbers are mm / N / MPa (the kernel's Law 12); pass units='in' for a "
            "data book row (inches, lbf, psi), or suffix any value ('13.75in', '3450lbf', "
            "'135psi'). Every answer carries both systems."
        ),
    }


__all__ = [
    "CITATIONS",
    "DEFINITIONS",
    "DEFINITIONS_ATTRIBUTION",
    "LBF_N",
    "PSI_MPA",
    "REFUSES",
    "SOURCE",
    "analyse",
    "contact_patch",
    "describe",
    "gyradius_mm",
    "load_at_inflation_n",
    "outside_diameter_from_circumference_mm",
    "percent_deflection_from_slr",
    "refusal",
    "refuse",
    "section_height_mm",
    "static_loaded_radius_mm",
    "vertical_rate_n_per_mm",
]
