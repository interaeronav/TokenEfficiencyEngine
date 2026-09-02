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
"""

from __future__ import annotations

import re
from typing import Any

from partkiln.data import load_table, provenance
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
    nominal, wanted_pitch = parse_designation(size)
    rows = load_table(filename)
    columns = [c for c in rows[0] if c.startswith(prefix + ":")]
    hits = [r for r in rows if _table_nominal(r["Size"]) == nominal]
    if wanted_pitch is not None:
        pitched = [r for r in hits if _table_pitch(r["Size"]) in (None, wanted_pitch)]
        hits = pitched or hits
    tabled = [r for r in hits if all(r[c] != "" for c in columns)]
    if not tabled:
        available = [
            _table_nominal(r["Size"])
            for r in rows
            if _table_nominal(r["Size"]) is not None and all(r[c] != "" for c in columns)
        ]
        raise _refuse(
            f"{key} does not table {size_key(nominal)}. Nearest tabled: "
            f"{_nearest([n for n in available if n is not None], nominal)}."
        )
    row = tabled[0]
    dims = {c.split(":", 1)[1]: row[c] for c in columns}
    row_pitch = _table_pitch(row["Size"])
    return {
        "standard": key,
        "size": size_key(nominal),
        "pitch_mm": row_pitch,
        "units": "in" if prefix.startswith("asme") else "mm",
        **dims,
        **_stamp(filename),
    }


__all__ = [
    "INCH_MM",
    "clearance_hole",
    "drill_size",
    "fastener",
    "parse_designation",
    "pitch",
    "size_key",
    "supported_standards",
    "tap_drill",
]
