"""Bill of materials: the `pk_bom` backend (D9), a pure read over an assembly.

Two views. `parts` aggregates by part: one row per distinct part with its
quantity (block + 4 pins -> `[{block, 1}, {pin, 4}]`), in order of first
use. `structured` lists every component instance in assembly order with
its component name. Either way a row is `{item, kind, part, qty, material,
mass_g, total_g, standard, components}` and the report ends with the
grand total.

Masses are rounded to 3 dp PER ROW before they are multiplied and summed,
so the printed rows add up to the printed total exactly (steel block
238.869 + 4 x 24.662 = 337.517 g; summing the unrounded products would
print 337.515 and fail arithmetic done by eye). `mass_g` comes straight
from the part card when it is there, else from `volume_mm3 x material`
through `partkiln.materials.mass_g` (the same rounding).

A card that can say NEITHER gets `mass_g: None`, never `0.000` (audited
defect, 2026-09-04): a zero both printed a mass the kernel does not know to
3 dp AND vanished silently from the sum, so a bill of materials understated
the assembly by a whole part while looking precise. Every such part is
named in `missing_mass` and `partial` is True, so `total_g` reads as the
lower bound it is (CLAUDE.md hard rule 6: fail loud, and name the fix -
here, the missing `material` or `mass_g`).

A `virtual` component (the contract's generic `create object`, D5) lands as
a row of kind `virtual` with whatever the card says - so a generic entity is
counted, never a refusal - and when the card says nothing its mass is `None`
too, on the same reasoning as defect 11 (audited 2026-09-04): a virtual
component is the unmodelled purchased part (a bearing, a fastener, glue), so
`0.000` is an understatement dressed as a measurement, not a fact. A caller
who means weightless writes `mass_g: 0` on the card and the row says 0.000.
"""

from __future__ import annotations

from typing import Any

from partkiln.assembly.model import Assembly, Component
from partkiln.document import CommandError

VIEWS = ("parts", "structured")


def _mass_g(card: dict[str, Any]) -> float | None:
    """One unit's mass in grams, or None when the card cannot say."""
    if card.get("mass_g") is not None:
        return round(float(card["mass_g"]), 3) + 0.0
    if card.get("volume_mm3") is not None and card.get("material"):
        from partkiln.materials import mass_g

        return mass_g(str(card["material"]), float(card["volume_mm3"]))
    return None


def _row(
    item: int,
    comp: Component,
    card: dict[str, Any],
    qty: int,
    components: list[str],
) -> dict[str, Any]:
    each = _mass_g(card)
    return {
        "item": item,
        "kind": "virtual" if comp.virtual else "part",
        "part": comp.part_name,
        "qty": qty,
        "material": str(card.get("material") or "none"),
        "mass_g": each,
        "total_g": None if each is None else round(each * qty, 3) + 0.0,
        "standard": str(card.get("standard_designation") or card.get("standard") or ""),
        "components": list(components),
    }


def bom(asm: Assembly, parts: dict[str, dict[str, Any]], view: str = "parts") -> dict[str, Any]:
    """`{view, rows, total_g, partial, missing_mass, count}` for the assembly.

    `parts` maps part name -> `{material, mass_g | volume_mm3, standard_designation}`;
    a component whose part has no card refuses naming the cards it does
    have, unless the component is virtual (then the row is empty of mass).
    A card that names neither a mass nor a material - and a virtual
    component with no card at all - leaves that row's `mass_g`/`total_g` at
    None: `total_g` then sums only the rows that HAVE a mass, `partial` is
    True and `missing_mass` names the parts to price.
    """
    if view not in VIEWS:
        raise CommandError(f"view {view!r} is not one of {', '.join(VIEWS)}.", code="pk_bad_op")
    cards = dict(parts or {})
    rows: list[dict[str, Any]] = []
    if view == "parts":
        groups: dict[str, list[Component]] = {}
        for comp in asm.components.values():
            groups.setdefault(comp.part_name, []).append(comp)
        for part, comps in groups.items():
            card = _card(part, comps[0], cards)
            rows.append(_row(len(rows) + 1, comps[0], card, len(comps), [c.name for c in comps]))
    else:
        for comp in asm.components.values():
            card = _card(comp.part_name, comp, cards)
            rows.append(_row(len(rows) + 1, comp, card, 1, [comp.name]))
    total = round(sum(r["total_g"] for r in rows if r["total_g"] is not None), 3) + 0.0
    # dict.fromkeys: first-use order, one entry per part even in the
    # structured view where every instance is its own row.
    missing = list(dict.fromkeys(r["part"] for r in rows if r["mass_g"] is None))
    return {
        "view": view,
        "rows": rows,
        "total_g": total,
        "partial": bool(missing),
        "missing_mass": missing,
        "count": sum(r["qty"] for r in rows),
    }


def _card(part: str, comp: Component, cards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if part in cards:
        return cards[part]
    if comp.virtual:
        return {}
    known = ", ".join(sorted(cards)) or "none"
    raise CommandError(
        f"no part card for {part!r} (component {comp.name!r}). Cards given: {known}. "
        "Pass parts={name: {material, mass_g | volume_mm3, standard_designation}}.",
        code="pk_ref_unknown",
    )


__all__ = ["VIEWS", "bom"]
