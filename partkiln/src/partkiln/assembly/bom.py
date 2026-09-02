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

A `virtual` component (the contract's generic `create object`, D5) lands as
a row of kind `virtual` with whatever the card says - nothing when it says
nothing - so a generic entity is counted, never a refusal.
"""

from __future__ import annotations

from typing import Any

from partkiln.assembly.model import Assembly, Component
from partkiln.document import CommandError

VIEWS = ("parts", "structured")


def _mass_g(part: str, card: dict[str, Any]) -> float:
    if "mass_g" in card and card["mass_g"] is not None:
        return round(float(card["mass_g"]), 3) + 0.0
    if card.get("volume_mm3") is not None and card.get("material"):
        from partkiln.materials import mass_g

        return mass_g(str(card["material"]), float(card["volume_mm3"]))
    return 0.0


def _row(
    item: int,
    comp: Component,
    card: dict[str, Any],
    qty: int,
    components: list[str],
) -> dict[str, Any]:
    each = _mass_g(comp.part_name, card)
    return {
        "item": item,
        "kind": "virtual" if comp.virtual else "part",
        "part": comp.part_name,
        "qty": qty,
        "material": str(card.get("material") or "none"),
        "mass_g": each,
        "total_g": round(each * qty, 3) + 0.0,
        "standard": str(card.get("standard_designation") or card.get("standard") or ""),
        "components": list(components),
    }


def bom(asm: Assembly, parts: dict[str, dict[str, Any]], view: str = "parts") -> dict[str, Any]:
    """`{view, rows, total_g, count}` for the assembly.

    `parts` maps part name -> `{material, mass_g | volume_mm3, standard_designation}`;
    a component whose part has no card refuses naming the cards it does
    have, unless the component is virtual (then the row is empty of mass).
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
    total = round(sum(r["total_g"] for r in rows), 3) + 0.0
    return {"view": view, "rows": rows, "total_g": total, "count": sum(r["qty"] for r in rows)}


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
