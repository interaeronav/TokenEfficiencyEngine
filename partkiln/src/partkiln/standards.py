"""Pure lookups over the shipped standards tables: the `pk_standards` backend.

"Clearance hole for an M6 bolt" is the single most common question a
mechanical model asks, and the single easiest one to answer from memory
wrongly (6.5? 6.4? 6.6?). Every answer here comes from a row in
`partkiln/data`, and every answer carries the authority (the standard), the
source URL and the licence of the table it came from, so the number can be
checked rather than trusted.

Designations are parsed tolerantly ('M6', 'm6', 'M6x1', 'M6-1', 'M6 x 1.0')
because the model is going to write all of them; a size that is not tabled
refuses with the nearest sizes that are, and an unknown standard refuses with
the ones that are supported. No OCP, no tee, no numpy.

ISO 286 limits and fits (`it_grade`, `deviation`, `limits`, `fit`) are the one
family here that is COMPUTED rather than looked up, and the reason is a
licence: no permissively-licensed reproduction of the ISO 286-1 tolerance
tables exists, and copying one is not an option. What ISO publishes as a
FORMULA may be implemented with a citation, so `data/iso286.json` holds the
formula parameters (clause 2.1.2's tolerance factor i = 0.45*D**(1/3) +
0.001*D, the grade multiples 7i/10i/16i/25i/40i/64i, the decade rule, and the
power laws for positions f, g, k, n) and partkiln does the arithmetic.

The standard's own rounding rules (clause 2.1.4) are NOT in the public text,
so the derivation does not reproduce every published value. Rather than serve
a number known to differ, every answer is checked against the size intervals
in `verified_exact_mm` - measured once against two independent reproductions
of ISO 286-1:2010 - and a size or grade outside them REFUSES `pk_not_served`,
naming the value that is missing and the `it_um` / `fd_um` the caller must
supply from a licensed copy. Positions that ISO tabulates rather than
computes (p, r, s, u, the J..ZC holes) refuse by name; they are not guessed.

ASME B18.3 is the one INCH standard shipped: its columns in `iso4762.csv` are
filled only on the imperial rows, which are spelled `#10-24`, `1/4-20`,
`1-8` - designation and threads per inch, never a metric nominal. Those
spellings are parsed here (`parse_imperial`), because a standard that
`supported_standards()` advertises and no input can reach is worse than one
that is not shipped at all.
"""

from __future__ import annotations

import math
import re
from typing import Any

from partkiln.data import load_json, load_table, provenance
from partkiln.document import CommandError

INCH_MM = 25.4

# Standard designation (normalised: upper, single space) -> (file, column prefix).
# bd_warehouse packs several standards per file with 'prefix:column' headers;
# this is the only place that packing is known.
_STANDARDS: dict[str, tuple[str, str]] = {
    "ISO 4762": ("iso4762.csv", "iso4762"),
    "ASME B18.3": ("iso4762.csv", "asme_b18.3"),
    "ISO 4014": ("iso4014_4017.csv", "iso4014"),
    "ISO 4017": ("iso4014_4017.csv", "iso4017"),
    "DIN 931": ("iso4014_4017.csv", "din931"),
    "ISO 4032": ("iso4032.csv", "iso4032"),
    "ISO 4033": ("iso4032.csv", "iso4033"),
    "ISO 4035": ("iso4032.csv", "iso4035"),
    "ISO 7089": ("iso7089.csv", "iso7089"),
    "ISO 7091": ("iso7089.csv", "iso7091"),
    "ISO 7093": ("iso7089.csv", "iso7093"),
    "ISO 7094": ("iso7089.csv", "iso7094"),
}

_CLEARANCE_SERIES = {"close": "Close", "normal": "Normal", "loose": "Loose"}

# The separator class takes the letter x, a typed multiplication sign
# (U+00D7, what a datasheet pastes) and a hyphen (bd_warehouse's spelling).
_DESIGNATION = re.compile(
    r"^\s*[Mm]?\s*(?P<nominal>\d+(?:\.\d+)?)\s*(?:[xX\u00d7\-]\s*(?P<pitch>\d+(?:\.\d+)?))?\s*$"
)
# An inch size as the ASME rows spell it: a gauge (`#10`) or a whole/fractional
# inch (`1`, `1/4`, `5/16`), then a hyphen, then threads per inch.
_IMPERIAL = re.compile(
    r"^\s*(?P<size>#\s*\d{1,2}|\d{1,2}\s*/\s*\d{1,2}|\d{1,2})"
    r"\s*[-xX\u00d7]\s*(?P<tpi>\d{1,3})\s*$"
)


def _refuse(message: str) -> CommandError:
    """A lookup that found nothing is a reference problem: D8 `pk_ref_unknown`."""
    return CommandError(message, code="pk_ref_unknown")


def parse_designation(text: str | float) -> tuple[float, float | None]:
    """'M6' -> (6.0, None); 'M6x0.75' / 'M6-0.75' / 'm6 x 0.75' -> (6.0, 0.75); 6 -> (6.0, None)."""
    if isinstance(text, int | float):
        return float(text), None
    match = _DESIGNATION.match(str(text))
    if not match:
        raise _refuse(
            f"{text!r} is not a metric thread designation. Write the nominal with an "
            "optional pitch: 'M6', 'M6x0.75' or 'M6-0.75'."
        )
    pitch = match.group("pitch")
    return float(match.group("nominal")), (float(pitch) if pitch is not None else None)


def parse_imperial(text: str | float) -> str:
    """'#10-24' / '1/4 - 20' / '1-8' -> the canonical row spelling, or a refusal.

    Metric and imperial spellings overlap ('1-8' would parse as M1 x 0.8), so
    only a lookup that already knows its standard is imperial comes here.
    """
    match = _IMPERIAL.match(str(text))
    if match is None:
        raise _refuse(
            f"{text!r} is not an inch fastener size. Write the designation and the threads "
            "per inch as the tables do: '#10-24', '1/4-20' or '1-8'."
        )
    size = re.sub(r"\s+", "", match.group("size"))
    return f"{size}-{int(match.group('tpi'))}"


def _table_imperial(size_cell: str | float) -> str | None:
    """The canonical inch spelling of a 'Size' cell; None for a metric row."""
    text = str(size_cell).strip()
    if text.startswith("M"):
        return None
    try:
        return parse_imperial(text)
    except CommandError:
        return None


def size_key(nominal: float) -> str:
    """6.0 -> 'M6', 1.6 -> 'M1.6' - the spelling the tables use."""
    return f"M{nominal:g}"


def _nearest(nominals: list[float], wanted: float, count: int = 3) -> str:
    ordered = sorted(set(nominals), key=lambda n: (abs(n - wanted), n))
    return ", ".join(size_key(n) for n in ordered[:count])


def _table_nominal(size_cell: str | float) -> float | None:
    """The nominal of a table 'Size' cell ('M6-1' -> 6.0); None for imperial rows."""
    text = str(size_cell).strip()
    if not text.startswith("M"):
        return None
    try:
        return parse_designation(text)[0]
    except ValueError:
        return None


def _table_pitch(size_cell: str | float) -> float | None:
    text = str(size_cell).strip()
    if not text.startswith("M"):
        return None
    return parse_designation(text)[1]


def _stamp(name: str, authority: str | None = None) -> dict[str, Any]:
    """The provenance triple every answer carries."""
    entry = provenance(name)
    return {
        "authority": authority or entry.get("authority", ""),
        "source": entry["source"],
        "licence": entry["licence"],
    }


def clearance_hole(size: str | float, series: str = "normal") -> dict[str, Any]:
    """ISO 273 clearance hole diameter for a bolt size, in the close/normal/loose series."""
    key = str(series).strip().lower()
    column = _CLEARANCE_SERIES.get(key)
    if column is None:
        raise _refuse(
            f"clearance series {series!r} is not one of close, normal, loose "
            "(ISO 273 fine / medium / coarse)."
        )
    nominal, _ = parse_designation(size)
    rows = load_table("clearance_holes.csv")
    nominals = [n for n in (_table_nominal(r["Size"]) for r in rows) if n is not None]
    for row in rows:
        if _table_nominal(row["Size"]) == nominal:
            return {
                "size": size_key(nominal),
                "series": key,
                "dia_mm": float(row[column]),
                "close_mm": float(row["Close"]),
                "normal_mm": float(row["Normal"]),
                "loose_mm": float(row["Loose"]),
                **_stamp("clearance_holes.csv", "ISO 273:1979"),
            }
    raise _refuse(
        f"{size_key(nominal)} has no ISO 273 clearance row. Nearest tabled: "
        f"{_nearest(nominals, nominal)}."
    )


def pitch(size: str | float) -> dict[str, Any]:
    """ISO 261 pitch for 'M6' (the coarse pitch) or 'M6x0.75' (that fine pitch, checked)."""
    nominal, wanted = parse_designation(size)
    rows = load_table("iso261_pitch.csv")
    same = [r for r in rows if float(r["nominal_mm"]) == nominal]
    if not same:
        nominals = [float(r["nominal_mm"]) for r in rows]
        raise _refuse(
            f"{size_key(nominal)} is not in the ISO 261 table. Nearest tabled: "
            f"{_nearest(nominals, nominal)}."
        )
    if wanted is None:
        coarse = [r for r in same if r["series"] == "coarse"]
        if not coarse:
            pitches = ", ".join(f"{float(r['pitch_mm']):g}" for r in same)
            raise _refuse(
                f"{size_key(nominal)} has no coarse pitch anchor in the source table; "
                f"name the pitch explicitly: {size_key(nominal)}x<pitch> with one of {pitches}."
            )
        row = coarse[0]
    else:
        hits = [r for r in same if float(r["pitch_mm"]) == wanted]
        if not hits:
            pitches = ", ".join(sorted({f"{float(r['pitch_mm']):g}" for r in same}, key=float))
            raise _refuse(
                f"{size_key(nominal)}x{wanted:g} is not an ISO 261 pitch for "
                f"{size_key(nominal)}. Tabled pitches: {pitches}."
            )
        row = hits[0]
    return {
        "designation": str(row["designation"]),
        "nominal_mm": nominal,
        "pitch_mm": float(row["pitch_mm"]),
        "series": str(row["series"]),
        **_stamp("iso261_pitch.csv", "ISO 261:1998"),
    }


def tap_drill(size: str | float) -> dict[str, Any]:
    """Tap drill for a thread: soft- and hard-material drills, soft served as `drill_mm`.

    'M6' resolves to the coarse pitch through ISO 261 first, because the tap
    table keys on 'M6-1' and a bare M6 would otherwise match nothing.
    """
    nominal, wanted = parse_designation(size)
    if wanted is None:
        wanted = pitch(nominal)["pitch_mm"]
    rows = load_table("tap_holes.csv")
    metric = [r for r in rows if _table_nominal(r["Size"]) is not None]
    for row in metric:
        if _table_nominal(row["Size"]) == nominal and _table_pitch(row["Size"]) == wanted:
            return {
                "size": f"{size_key(nominal)}x{wanted:g}",
                "pitch_mm": wanted,
                "drill_mm": float(row["Soft"]),
                "soft_mm": float(row["Soft"]),
                "hard_mm": float(row["Hard"]),
                **_stamp("tap_holes.csv"),
            }
    same = [r for r in metric if _table_nominal(r["Size"]) == nominal]
    if same:
        pitches = ", ".join(str(r["Size"]) for r in same)
        raise _refuse(
            f"{size_key(nominal)}x{wanted:g} has no tap-drill row. Tabled for this "
            f"nominal: {pitches}."
        )
    nominals = [n for n in (_table_nominal(r["Size"]) for r in metric) if n is not None]
    raise _refuse(
        f"{size_key(nominal)} has no tap-drill row. Nearest tabled: {_nearest(nominals, nominal)}."
    )


def drill_size(name: str) -> dict[str, Any]:
    """A letter or number drill ('A', '#7') in mm and inches."""
    wanted = str(name).strip().upper()
    rows = load_table("drill_sizes.csv")
    for row in rows:
        if str(row["Size"]).strip().upper() == wanted:
            inches = float(row["Diameter"])
            return {
                "size": str(row["Size"]).strip(),
                "dia_in": inches,
                "dia_mm": round(inches * INCH_MM, 3),
                **_stamp("drill_sizes.csv"),
            }
    raise _refuse(
        f"drill {name!r} is not tabled. Letter drills run A-Z and number drills #1-#80 "
        "(e.g. 'A', '#7')."
    )


def _tabled_sizes(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    """The 'Size' cells this standard actually fills - what a refusal must name."""
    return [str(r["Size"]).strip() for r in rows if all(r[c] != "" for c in columns)]


def _refuse_size(key: str, asked: str, sizes: list[str], nearest: str = "") -> CommandError:
    """A refusal that names the sizes that ARE available under `key`.

    The whole list up to 40 entries: no shipped standard fills more (ASME
    B18.3 fills 37, the widest), and half a list is what left the old refusal
    ending 'Nearest tabled: .' with no candidate a model could try.
    """
    shown = ", ".join(sizes[:40]) + (f" ... ({len(sizes)} total)" if len(sizes) > 40 else "")
    head = f"{key} does not table {asked}. "
    if nearest:
        head += f"Nearest tabled: {nearest}. "
    return _refuse(head + f"Tabled sizes: {shown or '(none)'}.")


def supported_standards() -> list[str]:
    return sorted(_STANDARDS)


def _normalise_standard(standard: str) -> str:
    text = re.sub(r"\s+", " ", str(standard).strip().upper())
    text = re.sub(r"^(ISO|DIN|ASME)(?=\d)", r"\1 ", text)
    return text


def fastener(standard: str, size: str | float) -> dict[str, Any]:
    """The tabled dimensions of one fastener: standard + size -> the row's columns, named.

    Empty cells mean the standard does not table that size (ISO 4033 has no
    M1.6, ISO 7093 no M1.7); those refuse rather than serve a blank as 0.
    """
    key = _normalise_standard(standard)
    if key not in _STANDARDS:
        raise _refuse(
            f"standard {standard!r} is not shipped. Supported: {', '.join(supported_standards())}."
        )
    filename, prefix = _STANDARDS[key]
    rows = load_table(filename)
    columns = [c for c in rows[0] if c.startswith(prefix + ":")]
    sizes = _tabled_sizes(rows, columns)
    if prefix.startswith("asme"):  # the one inch standard: its rows are #10-24, 1/4-20, 1-8
        try:
            wanted = parse_imperial(size)
        except CommandError:
            raise _refuse_size(
                key, f"{str(size)!r} (it is an INCH standard: designation-threads per inch)", sizes
            ) from None
        tabled = [
            r
            for r in rows
            if _table_imperial(r["Size"]) == wanted and all(r[c] != "" for c in columns)
        ]
        if not tabled:
            raise _refuse_size(key, wanted, sizes)
        row = tabled[0]
        return {
            "standard": key,
            "size": wanted,
            "tpi": int(wanted.rsplit("-", 1)[1]),
            "pitch_mm": None,
            "units": "in",
            **{c.split(":", 1)[1]: row[c] for c in columns},
            **_stamp(filename),
        }
    nominal, wanted_pitch = parse_designation(size)
    hits = [r for r in rows if _table_nominal(r["Size"]) == nominal]
    if wanted_pitch is not None:
        pitched = [r for r in hits if _table_pitch(r["Size"]) in (None, wanted_pitch)]
        hits = pitched or hits
    tabled = [r for r in hits if all(r[c] != "" for c in columns)]
    if not tabled:
        available = [
            n
            for n in (_table_nominal(r["Size"]) for r in rows if str(r["Size"]).strip() in sizes)
            if n is not None
        ]
        raise _refuse_size(key, size_key(nominal), sizes, _nearest(available, nominal))
    row = tabled[0]
    dims = {c.split(":", 1)[1]: row[c] for c in columns}
    row_pitch = _table_pitch(row["Size"])
    return {
        "standard": key,
        "size": size_key(nominal),
        "pitch_mm": row_pitch,
        "units": "mm",
        **dims,
        **_stamp(filename),
    }


# --------------------------------------------------------------------------- ISO 286 fits

ISO286_MAX_MM = 500.0
_FIT_TEXT = re.compile(
    r"^\s*(?:(?P<size>\d+(?:\.\d+)?)\s*)?(?P<hole>[A-Za-z]{1,2}\s*\d{1,2})"
    r"\s*[/-]\s*(?P<shaft>[A-Za-z]{1,2}\s*\d{1,2})\s*$"
)
_TOL_CLASS = re.compile(
    r"^\s*(?:(?P<size>\d+(?:\.\d+)?)\s*)?(?P<pos>[A-Za-z]{1,2})\s*(?P<grade>\d{1,2})\s*$"
)


def _iso286() -> dict[str, Any]:
    """The formula parameters, provenance-checked by the loader like every table."""
    return load_json("iso286.json")


def _not_served(message: str) -> CommandError:
    """A value ISO prints but partkiln will not derive: D8 `pk_not_served`.

    Distinct from `pk_ref_unknown` on purpose - the thing asked for exists in
    the standard, it is partkiln that declines, and the message must say what
    the caller has to supply instead.
    """
    return CommandError(message, code="pk_not_served")


def _round_um(value: float) -> int:
    """Round half UP, the way a tolerance table does; Python's round() is banker's."""
    return math.floor(value + 0.5)


def _covered(intervals: list[list[float]], size: float) -> bool:
    """`size` inside one half-open (lo, hi] interval - the ISO step convention."""
    return any(lo < size <= hi for lo, hi in intervals)


def _spell(intervals: list[list[float]]) -> str:
    return " and ".join(f"{lo:g}-{hi:g}" for lo, hi in intervals) + " mm"


def _size_step(size: float) -> list[float]:
    """The ISO 286 main size step holding `size`, or a refusal that names the range."""
    data = _iso286()
    if size <= 0 or size > ISO286_MAX_MM:
        raise _not_served(
            f"ISO 286 in partkiln is derived only for 0 < size <= {ISO286_MAX_MM:g} mm; "
            f"{size:g} mm needs the 500-3150 mm tolerance factor, which no primary text here "
            "verifies. Supply it_um and fd_um from a licensed ISO 286-1, or size it under 500 mm."
        )
    for lo, hi in data["size_steps_mm"]:
        if lo < size <= hi or (lo == 1 and size <= hi):
            return [lo, hi]
    raise _not_served(f"{size:g} mm falls in no ISO 286 main size step.")  # unreachable


def _factor_um(step: list[float]) -> tuple[float, float]:
    """(D, i) for a size step: clause 2.1.1's geometric mean and clause 2.1.2.1's factor."""
    D = math.sqrt(step[0] * step[1])
    return D, 0.45 * D ** (1.0 / 3.0) + 0.001 * D


def _iso_stamp(data: dict[str, Any]) -> dict[str, Any]:
    entry = provenance("iso286.json")
    return {
        "authority": data["authority"],
        "source": entry["source"],
        "licence": entry["licence"],
    }


def it_grade(size: float, grade: int, *, it_um: float | None = None) -> dict[str, Any]:
    """The ISO 286 standard tolerance IT<grade> at `size`, in micrometres.

    Computed from clause 2.1.2's formula, never read from a table, and served
    only where that arithmetic was verified to land on the published value.
    `it_um` overrides the derivation with a value the caller read from their
    own licensed copy; the answer then says `basis: supplied`.
    """
    data = _iso286()
    step = _size_step(float(size))
    D, i = _factor_um(step)
    out: dict[str, Any] = {
        "grade": f"IT{int(grade)}",
        "size_mm": float(size),
        "step_mm": step,
        "D_mm": round(D, 4),
        "i_um": round(i, 4),
        **_iso_stamp(data),
    }
    if it_um is not None:
        return {**out, "it_um": float(it_um), "basis": "supplied", "formula": "supplied by caller"}
    key = str(int(grade))
    intervals = data["verified_exact_mm"]["it"].get(key)
    if intervals is None:
        why = data["grades_not_derivable"]
        reason = why.get(_reason_key(int(grade)), "no public formula reaches it")
        served = ", ".join(
            f"IT{g}" for g in sorted(int(k) for k in data["verified_exact_mm"]["it"])
        )
        raise _not_served(
            f"IT{int(grade)} is not derivable: {reason} Supply it_um from ISO 286-1 Table 1, "
            f"or use a grade partkiln derives: {served}."
        )
    raw = _derive_it(data, step, int(grade))
    value = _round_um(raw)
    if not _covered(intervals, float(size)):
        raise _not_served(
            f"IT{int(grade)} at {size:g} mm (step {step[0]:g}-{step[1]:g} mm) derives as "
            f"{value} um, but ISO 286-1's published IT{int(grade)} rounds differently in that "
            f"step, so partkiln will not serve it. Supply it_um from ISO 286-1 Table 1. "
            f"IT{int(grade)} is served for {_spell(intervals)}."
        )
    return {
        **out,
        "it_um": value,
        "it_raw_um": round(raw, 4),
        "basis": "derived",
        "formula": data["tolerance_factor"]["expression"] + f"; IT{int(grade)} from the multiples",
    }


def _derive_it(data: dict[str, Any], step: list[float], grade: int) -> float:
    """IT in micrometres, unrounded except where the standard's own footnote rounds."""
    if grade > 10:  # the decade rule: IT(n+5) = 10 * IT(n) for n >= 6
        return 10.0 * _round_um(_derive_it(data, step, grade - 5))
    exception = data["grade_exception"]
    if grade == exception["grade"] and step == list(exception["step_mm"]):
        return float(exception["value_um"])
    _D, i = _factor_um(step)
    return float(data["grade_multiples_of_i"][str(grade)]) * i


def _reason_key(grade: int) -> str:
    """Which `grades_not_derivable` entry explains this grade's refusal."""
    if grade <= 1:
        return "1"
    if grade <= 4:
        return "2"
    return "17"


def _fd_limit(letter: str) -> str:
    """Which of the two deviations IS the fundamental one for this position.

    ISO 286's positions run a..h then js, j..zc: for a shaft the first group's
    fundamental deviation is the UPPER one (es, at or below the zero line) and
    the second group's is the LOWER one (ei); a hole of the same letter is the
    mirror image, so the groups swap. Two-letter positions (cd, ef, fg, za)
    are grouped by their first letter, which is where they sit on the diagram.
    """
    is_hole = letter[0].isupper()
    first_group = letter[0].lower() <= "h"
    if is_hole:
        return "lower" if first_group else "upper"
    return "upper" if first_group else "lower"


def _position(data: dict[str, Any], letter: str) -> dict[str, Any]:
    """The position card for a letter, or a refusal that names why it is absent."""
    positions = data["positions"]
    if letter in positions:
        return positions[letter]
    if not letter.isalpha() or len(letter) > 2:
        raise _refuse(
            f"{letter!r} is not an ISO 286 position letter. Write a class as letter+grade: "
            "'H7', 'g6', 'js6'."
        )
    served = ", ".join(sorted(positions))
    for group, why in data["positions_not_derivable"].items():
        if letter in group.replace("(holes)", "").replace("..", " ").split():
            raise _not_served(
                f"fundamental deviation {letter!r} is tabulated in ISO 286-1, not computed: "
                f"{why} Supply fd_um (the signed fundamental deviation in um) for this class, "
                f"or use a served position: {served}."
            )
    raise _not_served(
        f"position {letter!r} is not one partkiln derives. Served: {served}. "
        "Supply fd_um for anything else."
    )


def _derive_fd(
    data: dict[str, Any],
    card: dict[str, Any],
    letter: str,
    size: float,
    grade: int,
    step: list[float],
) -> float:
    """The fundamental deviation of a served position, in micrometres.

    A `mirror` hole is its shaft's deviation negated (the general rule
    EI = -es), so it is checked against the SHAFT's verified interval - the
    hole was never separately compared with a published value.
    """
    if card["rule"] == "zero":
        return 0.0
    source = data["positions"][card["of"]] if card["rule"] == "mirror" else card
    checked = card["of"] if card["rule"] == "mirror" else letter
    grades = card.get("grades")
    if grades is not None and int(grade) not in grades:
        raise _not_served(
            f"position {letter!r} is derived only for grades "
            f"{', '.join('IT' + str(g) for g in grades)}; ISO 286-1 tabulates it for "
            f"IT{int(grade)}. Supply fd_um for {letter}{int(grade)}."
        )
    intervals = data["verified_exact_mm"]["position"][checked]
    if not _covered(intervals, float(size)):
        raise _not_served(
            f"the fundamental deviation of {letter!r} at {size:g} mm derives, but in the step "
            f"{step[0]:g}-{step[1]:g} mm it was not verified against a published value, so "
            f"partkiln will not serve it. Supply fd_um. {letter!r} is served for "
            f"{_spell(intervals)}."
        )
    D, _i = _factor_um(step)
    magnitude = _round_um(float(source["coefficient"]) * D ** float(source["exponent"]))
    signed = float(source["sign"]) * magnitude
    return -signed if card["rule"] == "mirror" else signed


def deviation(
    size: float,
    position: str,
    grade: int,
    *,
    it_um: float | None = None,
    fd_um: float | None = None,
) -> dict[str, Any]:
    """The (es, ei) of a shaft or the (ES, EI) of a hole, in micrometres.

    `fd_um` supplies the fundamental deviation (signed, the one nearest the
    zero line) for a position partkiln refuses to derive, and `it_um` supplies
    the tolerance the same way; either makes that half of the answer
    `basis: supplied`. With `fd_um` given the position letter is not looked up
    at all, so a caller holding ISO 286-1 can spell any class in the system.
    """
    data = _iso286()
    letter = str(position).strip()
    it = it_grade(size, grade, it_um=it_um)
    value = float(it["it_um"])
    step = it["step_mm"]
    if fd_um is None:
        card = _position(data, letter)
        applies, rule, text = card["applies"], card["rule"], card["text"]
        fundamental = (
            0.0
            if rule == "symmetric"
            else _derive_fd(data, card, letter, float(size), int(grade), step)
        )
        basis = it["basis"]
    else:
        applies = "hole" if letter[:1].isupper() else "shaft"
        rule, text = "supplied", f"fundamental deviation {float(fd_um):+g} um supplied by caller"
        fundamental = float(fd_um)
        basis = "supplied"
    if rule == "symmetric":
        upper, lower = value / 2.0, -value / 2.0
        fundamental = upper
    elif _fd_limit(letter) == "upper":
        upper, lower = fundamental, fundamental - value
    else:
        upper, lower = fundamental + value, fundamental
    return {
        "class": f"{letter}{int(grade)}",
        "position": letter,
        "applies": applies,
        "size_mm": float(size),
        "step_mm": step,
        "it_um": value,
        "upper_um": round(upper, 4),
        "lower_um": round(lower, 4),
        "fundamental_um": round(fundamental, 4),
        "basis": basis,
        "rule": text,
        **_iso_stamp(data),
    }


def limits(
    size: float, tol_class: str, *, it_um: float | None = None, fd_um: float | None = None
) -> dict[str, Any]:
    """'20 H7' -> the two limits of size in mm, with the deviations that made them."""
    match = _TOL_CLASS.match(str(tol_class))
    if not match:
        raise _refuse(
            f"{tol_class!r} is not an ISO 286 tolerance class. Write letter+grade, "
            "optionally after the size: 'H7', 'g6', '20H7'."
        )
    if match.group("size") is not None:
        size = float(match.group("size"))
    dev = deviation(size, match.group("pos"), int(match.group("grade")), it_um=it_um, fd_um=fd_um)
    lower = float(size) + dev["lower_um"] / 1000.0
    upper = float(size) + dev["upper_um"] / 1000.0
    return {**dev, "min_mm": round(lower, 4), "max_mm": round(upper, 4)}


def fit(
    designation: str, size: float | None = None, *, supplied: dict[str, Any] | None = None
) -> dict[str, Any]:
    """'20H7/g6' -> both members' limits and the clearance or interference between them.

    `supplied` maps a class spelling to the values a licensed ISO 286-1 gives,
    e.g. `{"p6": {"fd_um": 22}}`, for the positions partkiln refuses to derive.
    """
    match = _FIT_TEXT.match(str(designation))
    if not match:
        raise _refuse(
            f"{designation!r} is not an ISO 286 fit. Write hole/shaft after the size: "
            "'20H7/g6' (or pass size separately and write 'H7/g6')."
        )
    if match.group("size") is not None:
        size = float(match.group("size"))
    if size is None:
        raise CommandError(
            f"fit {designation!r} needs a nominal size: write '20H7/g6' or pass size=20.",
            code="pk_needs",
        )
    given = {str(k).replace(" ", ""): dict(v) for k, v in (supplied or {}).items()}
    members = []
    for part in (match.group("hole"), match.group("shaft")):
        spelling = re.sub(r"\s+", "", part)
        members.append(limits(float(size), spelling, **given.get(spelling, {})))
    hole, shaft = members
    if hole["applies"] != "hole" or shaft["applies"] != "shaft":
        raise _refuse(
            f"{designation!r} reads as {hole['class']}/{shaft['class']}: the hole (a CAPITAL "
            "letter) is written first, the shaft (lower case) second."
        )
    min_clearance = hole["lower_um"] - shaft["upper_um"]
    max_clearance = hole["upper_um"] - shaft["lower_um"]
    if min_clearance >= 0:
        kind = "clearance"
    elif max_clearance <= 0:
        kind = "interference"
    else:
        kind = "transition"
    basis = "supplied" if "supplied" in (hole["basis"], shaft["basis"]) else "derived"
    return {
        "designation": f"{size:g} {hole['class']}/{shaft['class']}",
        "size_mm": float(size),
        "step_mm": hole["step_mm"],
        "kind": kind,
        "hole": {
            k: hole[k] for k in ("class", "it_um", "upper_um", "lower_um", "min_mm", "max_mm")
        },
        "shaft": {
            k: shaft[k] for k in ("class", "it_um", "upper_um", "lower_um", "min_mm", "max_mm")
        },
        "min_clearance_um": round(min_clearance, 4),
        "max_clearance_um": round(max_clearance, 4),
        "basis": basis,
        **_iso_stamp(_iso286()),
    }


def supported_fits() -> dict[str, Any]:
    """What the fit lane derives, what it refuses, and where each is served."""
    data = _iso286()
    verified = data["verified_exact_mm"]
    return {
        "grades": {
            f"IT{g}": _spell(v)
            for g, v in sorted(verified["it"].items(), key=lambda kv: int(kv[0]))
        },
        "positions": {p: _spell(v) for p, v in sorted(verified["position"].items())},
        "refused": data["positions_not_derivable"],
        "size_range_mm": [0, ISO286_MAX_MM],
        "note": (
            "every value is COMPUTED from ISO 286-1's published formulae, never copied from a "
            "tolerance table; outside the ranges above partkiln refuses and asks for it_um / fd_um."
        ),
        **_iso_stamp(data),
    }


__all__ = [
    "INCH_MM",
    "ISO286_MAX_MM",
    "clearance_hole",
    "deviation",
    "drill_size",
    "fastener",
    "fit",
    "it_grade",
    "limits",
    "parse_designation",
    "parse_imperial",
    "pitch",
    "size_key",
    "supported_fits",
    "supported_standards",
    "tap_drill",
]
