"""Material cards with an honesty tier per value: the `pk_materials` backend.

A density is the one material fact a CAD kernel USES (mass = volume x rho);
E and yield are what a check reads. Every value on a card says where it came
from and how much to trust it - `standard_value` is the number a named
standard prints, `datasheet` a grade datasheet class, `typical_range` a
handbook range served as its midpoint with the range beside it, `derived`
computed here. The discipline is TEE's own (server/src/tee/physical/
materials.py): no bulk-scraped sources, and a range never masquerades as a
standard number. Assignment is `set part material=` in a batch; this module
never touches a document.
"""

from __future__ import annotations

from functools import cache
from typing import Any

from partkiln.data import DataError, load_json
from partkiln.document import CommandError

HONESTY_TIERS = ("standard_value", "datasheet", "typical_range", "derived")

# Volume arrives in mm3 and density in kg/m3; the answer is grams.
# 1 mm3 = 1e-9 m3 and 1 kg = 1000 g, so g = mm3 * kg/m3 * 1e-6.
_G_PER_MM3_PER_KGM3 = 1e-6


@cache
def _cards() -> dict[str, dict[str, Any]]:
    doc = load_json("materials.json")
    cards = doc["cards"]
    for name, card in cards.items():
        _validate(name, card)
    return cards


def _validate(name: str, card: dict[str, Any]) -> None:
    """A card is refused at load, not at use, when a value lacks its paper trail."""
    props = card.get("properties", {})
    if "density" not in props:
        raise DataError(f"material card {name!r} has no density; mass_g would have nothing to use.")
    for prop, leaf in props.items():
        for key in ("value", "unit", "source", "honesty"):
            if key not in leaf or leaf[key] in ("", None):
                raise DataError(
                    f"material card {name!r}.{prop} lacks {key!r}. Every value is "
                    "{value, unit, source, honesty}; fill it in partkiln/data/materials.json."
                )
        if leaf["honesty"] not in HONESTY_TIERS:
            raise DataError(
                f"material card {name!r}.{prop} has honesty {leaf['honesty']!r}; "
                f"allowed: {', '.join(HONESTY_TIERS)}."
            )
        if leaf["honesty"] == "typical_range" and "range" not in leaf:
            raise DataError(
                f"material card {name!r}.{prop} is typical_range without a range; "
                "state [low, high] beside the midpoint."
            )


def names() -> list[str]:
    return sorted(_cards())


def resolve(name: str) -> str:
    """The card key for a name or alias ('steel', 's275', '304' ...); refuses listing names."""
    wanted = str(name).strip().lower()
    cards = _cards()
    if wanted in cards:
        return wanted
    for key, card in cards.items():
        if wanted in (alias.lower() for alias in card.get("aliases", [])):
            return key
    raise CommandError(
        f"no material {name!r}. Cards: {', '.join(names())} (aliases such as 'steel', "
        "'304' or '6061' are accepted).",
        code="pk_ref_unknown",
    )


def card(name: str) -> dict[str, Any]:
    """One card, every value with its unit, source and honesty."""
    key = resolve(name)
    return {"name": key, **_cards()[key]}


def cards() -> list[dict[str, Any]]:
    """Every card, in name order."""
    return [card(key) for key in names()]


def density_kg_m3(name: str) -> float:
    return float(card(name)["properties"]["density"]["value"])


def mass_g(name: str, volume_mm3: float) -> float:
    """Mass in grams for a solid volume, rounded to 3 dp (W1 bracket: 91 158.6 mm3 -> 715.595 g).

    Rounded BEFORE it goes on the wire so two kernels computing the same part
    print the same gram, the determinism law applied to a float product.
    """
    if volume_mm3 < 0:
        raise CommandError(
            f"volume {volume_mm3} mm3 is negative; a solid's volume is never negative - "
            "check the boolean that produced it.",
            code="pk_needs",
        )
    return round(float(volume_mm3) * density_kg_m3(name) * _G_PER_MM3_PER_KGM3, 3)


def describe(name: str) -> dict[str, Any]:
    """The card flattened for a reader: one line per value with its honesty and source.

    `values` maps property -> number; `honesty` and `sources` map the same keys,
    so a caller can print a fact and its trust side by side without walking the
    nested card. `notes` is one line per material fact (D7).
    """
    full = card(name)
    values: dict[str, float] = {}
    units: dict[str, str] = {}
    honesty: dict[str, str] = {}
    sources: dict[str, str] = {}
    ranges: dict[str, list[float]] = {}
    notes: list[str] = []
    for prop, leaf in full["properties"].items():
        values[prop] = leaf["value"]
        units[prop] = leaf["unit"]
        honesty[prop] = leaf["honesty"]
        sources[prop] = leaf["source"]
        line = f"{prop} = {leaf['value']:g} {leaf['unit']} ({leaf['honesty']}: {leaf['source']})"
        if "range" in leaf:
            low, high = leaf["range"]
            ranges[prop] = [low, high]
            line += f", range {low:g}-{high:g}"
        notes.append(line)
    if full.get("notes"):
        notes.append(full["notes"])
    return {
        "name": full["name"],
        "designation": full.get("designation", ""),
        "family": full.get("family", ""),
        "values": values,
        "units": units,
        "honesty": honesty,
        "sources": sources,
        "ranges": ranges,
        "notes": notes,
    }


__all__ = [
    "HONESTY_TIERS",
    "card",
    "cards",
    "density_kg_m3",
    "describe",
    "mass_g",
    "names",
    "resolve",
]
