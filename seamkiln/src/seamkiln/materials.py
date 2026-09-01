"""The material library: cards, categories, custom cloth, and files.

`fabric.py` holds the bundled cards and the physics they map to. This is the
library around them - searching, filtering, adding your own, and getting them
in and out of files - because a fabric card is a document a studio owns, not a
constant in someone's source.

The tier flag travels through every one of those doors. A card imported from
a file arrives with whatever tier it claims; a card *derived* from a KES-F or
fabric-kit test may claim `measured` and must name its report. Nothing here
promotes a card's tier on its own, because that is how a solver constant ends
up on a spec sheet as a measurement.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from seamkiln.pattern.fabric import _TABLE, Fabric, Tier

# What a cloth is FOR, which is how a designer looks for one - not by GSM.
CATEGORIES: dict[str, tuple[str, ...]] = {
    "shirting": ("cotton_poplin",),
    "knit": ("cotton_jersey",),
    "denim": ("denim_12oz",),
    "lining": ("silk_habotai",),
    "tailoring": ("wool_suiting",),
    "leather": ("leather_garment",),
    "sheer": ("chiffon",),
}

# Ranges a card has to sit inside to be plausible at all. A "fabric" at
# 5,000 g/m2 is a mistake, not a material, and catching it at the door beats
# discovering it as a solver that will not converge.
LIMITS: dict[str, tuple[float, float]] = {
    "gsm": (5.0, 2000.0),
    "thickness_mm": (0.01, 8.0),
    "bend_warp": (0.05, 5000.0),  # flexural rigidity, mN.mm
    "bend_weft": (0.05, 5000.0),
    "friction": (0.02, 1.2),
}


class MaterialError(ValueError):
    """A card that cannot be a cloth."""


def validate(card: Fabric) -> Fabric:
    """Refuse a card that is not a material, and say which field."""
    for field_name, (low, high) in LIMITS.items():
        value = float(getattr(card, field_name))
        if not low <= value <= high:
            raise MaterialError(
                f"{card.name}: {field_name} = {value:g} is outside {low:g}-{high:g}. "
                "Flexural rigidity is in mN.mm and weight in g/m2 - a common cause "
                "is a card written in different units."
            )
    if card.tier is Tier.MEASURED and not card.source:
        raise MaterialError(
            f"{card.name}: tier 'measured' needs a `source` naming the test report. "
            "A card that claims a measurement without one is a solver constant "
            "wearing a lab coat."
        )
    return card


def library(category: str | None = None, *, tier: str | None = None) -> list[dict[str, Any]]:
    """The catalogue, filterable the way a designer actually filters."""
    names = CATEGORIES.get(category, ()) if category is not None else tuple(sorted(_TABLE))
    if category is not None and not names:
        raise KeyError(f"no category {category!r}; categories: {', '.join(sorted(CATEGORIES))}.")
    rows = []
    for name in names:
        card = _TABLE[name]
        if tier and str(card.tier) != tier:
            continue
        rows.append(
            {
                "name": card.name,
                "category": category_of(card.name),
                "gsm": card.gsm,
                "thickness_mm": card.thickness_mm,
                "rigidity_mNmm": round((card.bend_warp + card.bend_weft) / 2, 1),
                "tier": str(card.tier),
                "notes": card.notes,
            }
        )
    return rows


def category_of(name: str) -> str:
    for category, members in CATEGORIES.items():
        if name in members:
            return category
    return "custom"


def add(card: Fabric, *, category: str = "custom", overwrite: bool = False) -> Fabric:
    """Register a custom cloth. Refuses to shadow a bundled card silently."""
    validate(card)
    if card.name in _TABLE and not overwrite:
        raise MaterialError(
            f"{card.name!r} is already in the library. Pass overwrite=True to "
            "replace it, or give the card a different name - two cloths with one "
            "name is how a tech pack ends up describing the wrong cloth."
        )
    _TABLE[card.name] = card
    CATEGORIES.setdefault(category, ())
    CATEGORIES[category] = tuple(sorted({*CATEGORIES[category], card.name}))
    return card


def derive(base: str, name: str, **changes: Any) -> Fabric:
    """A variant of an existing cloth - a heavier denim, a softer poplin.

    The derived card inherits the base's tier and drops to `plausible` the
    moment a physical field changes, because a measured denim's test report
    does not describe a denim you made 20% heavier.
    """
    card = _TABLE.get(base)
    if card is None:
        raise KeyError(f"no material {base!r}; have: {', '.join(sorted(_TABLE))}.")
    physical = {
        "gsm",
        "thickness_mm",
        "bend_warp",
        "bend_weft",
        "tensile_warp",
        "tensile_weft",
        "shear",
        "friction",
    }
    tier = Tier.PLAUSIBLE if physical & set(changes) else card.tier
    source = "" if tier is Tier.PLAUSIBLE else card.source
    return validate(
        replace(card, name=name, tier=tier, source=source, notes=f"derived from {base}", **changes)
    )


def to_file(names: list[str] | None, path: str | Path) -> dict[str, Any]:
    """Write cards to a portable JSON file - the studio's own library."""
    chosen = names or sorted(_TABLE)
    missing = [n for n in chosen if n not in _TABLE]
    if missing:
        raise KeyError(f"not in the library: {', '.join(missing)}")
    payload = {
        "seamkiln_materials": 1,
        "cards": [
            {**asdict(_TABLE[n]), "tier": str(_TABLE[n].tier), "category": category_of(n)}
            for n in chosen
        ],
    }
    destination = Path(path)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"path": str(destination), "cards": len(chosen)}


def from_file(path: str | Path, *, overwrite: bool = False) -> list[str]:
    """Read a material file, validating every card on the way in."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("seamkiln_materials") != 1:
        raise MaterialError(
            f"{path} is not a seamkiln material file (version {data.get('seamkiln_materials')!r})."
        )
    loaded: list[str] = []
    for row in data.get("cards", []):
        row = dict(row)
        category = row.pop("category", "custom")
        row["tier"] = Tier(row.get("tier", "plausible"))
        card = Fabric(**row)
        add(card, category=category, overwrite=overwrite)
        loaded.append(card.name)
    return loaded


def compare(names: list[str]) -> dict[str, Any]:
    """Side by side: what actually differs between two cloths."""
    cards = []
    for name in names:
        if name not in _TABLE:
            raise KeyError(f"no material {name!r}")
        cards.append(_TABLE[name])
    return {
        "materials": [c.name for c in cards],
        "rows": {
            "gsm": [c.gsm for c in cards],
            "thickness_mm": [c.thickness_mm for c in cards],
            "rigidity_mNmm": [round((c.bend_warp + c.bend_weft) / 2, 1) for c in cards],
            "bending_alpha": [round(c.compliances()["bending"], 4) for c in cards],
            "stretch_warp": [round(c.compliances()["stretch_warp"], 4) for c in cards],
            "tier": [str(c.tier) for c in cards],
        },
        "note": "bending_alpha is weight over rigidity - the ratio drape depends on",
    }
