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
        _validate_anisotropy(name, card)
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


def _validate_anisotropy(name: str, card: dict[str, Any]) -> None:
    """An anisotropic card must say WHICH scalars it will not invent, and why.

    A card that simply omits `E` reads as "not recorded yet", and the next
    reader supplies one from memory - which for a laminate is the failure this
    whole tier system exists to stop. So an anisotropic card carries a
    `refuses` entry per isotropic scalar, each with a reason and a fix, and
    `property_value` raises it rather than returning nothing.
    """
    refuses = card.get("refuses")
    if not card.get("anisotropic"):
        # An ISOTROPIC card may still refuse. The quasi-isotropic laminate is
        # genuinely isotropic in-plane and serves E, yet its strength depends
        # on the stacking sequence and is refused. So validate whatever is
        # declared; only REQUIRE a declaration when the card says its
        # properties have a direction.
        if refuses is not None:
            _validate_refusals(name, card, refuses)
        return
    if not isinstance(refuses, dict) or not refuses:
        raise DataError(
            f"material card {name!r} is anisotropic but lists no `refuses`; say which "
            "scalars it will not invent (E, yield, G, nu) with a reason and a fix."
        )
    _validate_refusals(name, card, refuses)


def _validate_refusals(name: str, card: dict[str, Any], refuses: Any) -> None:
    """Every declared refusal names a reason AND a fix, and refuses nothing served."""
    if not isinstance(refuses, dict):
        raise DataError(f"material card {name!r}.refuses must map a property to its reason.")
    for prop, entry in refuses.items():
        for key in ("reason", "fix"):
            if not isinstance(entry, dict) or not entry.get(key):
                raise DataError(
                    f"material card {name!r}.refuses.{prop} has no {key!r}; a refusal "
                    "names its reason and the fix."
                )
        if prop in card["properties"]:
            raise DataError(f"material card {name!r} both serves and refuses {prop!r}; pick one.")


ANISOTROPIC_HINT = (
    "This card is anisotropic: its stiffness and strength depend on the direction of "
    "the load, so it serves direction-named values instead."
)


# Names people reasonably ask this lane for that are NOT materials. A tyre is a
# STRUCTURE - several rubber compounds, textile or steel cords, belts and a bead
# - so it has a vertical stiffness in N/mm, not a modulus in N/mm2, and no
# density that means anything for a part's mass. Answering with a rubber card
# would be a confident wrong answer of the worst kind, so each of these refuses
# and says what IS knowable.
_NOT_A_MATERIAL: dict[str, tuple[str, str]] = {
    "tyre": (
        "a tyre is a structure, not a material: several rubber compounds over textile or "
        "steel cords, with a bead and belts, so its stiffness is a vertical rate in N/mm "
        "that depends on inflation pressure, not a modulus",
        "for the rubber itself see rubber_nbr or rubber_epdm; for the tyre, take a vertical "
        "and lateral stiffness from its manufacturer's load-deflection data at your pressure",
    ),
    "f1 tyre": (
        "Formula 1 compounds are trade secrets. Pirelli publishes the compound DESIGNATIONS "
        "(C1 hardest to C5 softest), their operating temperature windows and the tyre "
        "dimensions - and no compound properties whatever: no density, no modulus, no "
        "filler loading. Nothing in this lane could serve one without inventing it",
        "model the tyre as a structure with a measured vertical stiffness, or use a generic "
        "filled elastomer (rubber_nbr, rubber_epdm) and say in your report that it is a "
        "stand-in, not a compound",
    ),
    "aircraft tyre": (
        "aircraft tyre makers publish load, speed, inflation and dimension tables - the "
        "data a landing gear engineer actually needs - and not the compound properties. A "
        "tyre is also a pressure vessel here: most of its load capacity is the inflation "
        "gas, not the rubber",
        "take rated load, pressure and deflection from the manufacturer's aircraft tyre "
        "data book; for the rubber alone see rubber_nbr or rubber_epdm",
    ),
}
_NOT_A_MATERIAL_ALIASES = {
    "tire": "tyre",
    "tyres": "tyre",
    "tires": "tyre",
    "rubber tyre": "tyre",
    "f1 tire": "f1 tyre",
    "formula 1 tyre": "f1 tyre",
    "formula 1 tire": "f1 tyre",
    "formula one tyre": "f1 tyre",
    "racing tyre": "f1 tyre",
    "racing tire": "f1 tyre",
    "aircraft tire": "aircraft tyre",
    "aeroplane tyre": "aircraft tyre",
    "airplane tire": "aircraft tyre",
    "aeroplane tire": "aircraft tyre",
    "aviation tyre": "aircraft tyre",
    "aviation tire": "aircraft tyre",
}


def names() -> list[str]:
    return sorted(_cards())


def resolve(name: str) -> str:
    """The card key for a name or alias ('s275', '304', '6061'); refuses listing names."""
    wanted = str(name).strip().lower()
    cards = _cards()
    if wanted in cards:
        return wanted
    for key, card in cards.items():
        if wanted in (alias.lower() for alias in card.get("aliases", [])):
            return key
    not_material = _NOT_A_MATERIAL.get(_NOT_A_MATERIAL_ALIASES.get(wanted, wanted))
    if not_material is not None:
        reason, fix = not_material
        raise CommandError(f"{name!r} is not a material: {reason}. Fix: {fix}.", code="pk_needs")
    family = [key for key in cards if key.startswith(f"{wanted}_")]
    if family:
        # A family name is not a material. "cfrp" spans an order of magnitude in
        # stiffness across layups; "titanium" spans 3.15x in yield between CP
        # Grade 2 and Ti-6Al-4V. Picking one silently answers a question the
        # caller never asked, so name them and let the caller choose.
        raise CommandError(
            f"{name!r} names a family, not one material, and the cards in it differ enough "
            f"that picking one would be a guess: {', '.join(sorted(family))}. Name the one "
            "you mean.",
            code="pk_ref_ambiguous",
        )
    raise CommandError(
        f"no material {name!r}. Cards: {', '.join(names())} (aliases such as 's275', "
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


def property_value(name: str, prop: str) -> float:
    """One property of one card, or a refusal that says why it does not exist.

    `density` always answers - it is direction-free and it is what mass uses.
    A scalar an anisotropic card deliberately does not carry raises with the
    reason and the fix, so nobody fills the silence from memory.
    """
    full = card(name)
    leaf = full["properties"].get(prop)
    if leaf is not None:
        return float(leaf["value"])
    refused = (full.get("refuses") or {}).get(prop)
    if refused is not None:
        raise CommandError(
            f"{full['name']} does not carry {prop!r}: {refused['reason']}. Fix: {refused['fix']}.",
            code="pk_needs",
        )
    served = ", ".join(sorted(full["properties"]))
    raise CommandError(
        f"{full['name']} has no {prop!r}. It carries: {served}.",
        code="pk_ref_unknown",
    )


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
    for prop, entry in (full.get("refuses") or {}).items():
        notes.append(f"{prop} = REFUSED: {entry['reason']}. Fix: {entry['fix']}.")
    if full.get("anisotropic"):
        notes.append(ANISOTROPIC_HINT)
    if full.get("notes"):
        notes.append(full["notes"])
    return {
        "name": full["name"],
        "designation": full.get("designation", ""),
        "family": full.get("family", ""),
        "values": values,
        "units": units,
        "honesty": honesty,
        "anisotropic": bool(full.get("anisotropic")),
        "refuses": {p: e["reason"] for p, e in (full.get("refuses") or {}).items()},
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
