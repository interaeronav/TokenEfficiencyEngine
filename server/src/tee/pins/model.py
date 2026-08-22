"""Pin <-> actor-tag encoding. Pure functions: no editor, no I/O.

Tags are the storage. One marker tag says "this actor is a pin"; the rest are
`<namespace>_<field>:<value>` pairs. Values are split on the FIRST colon only,
so an asset key like `polyhaven:bar_chair_round_01` survives a round trip.
"""

from __future__ import annotations

import re
from typing import Any

from tee.kernel.errors import TeeError

#: Wishlist terms and target dims are lists inside one tag; this separates
#: them. It is the one character a term may not contain.
LIST_SEP = "|"

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,47}$")

#: field name -> tag suffix. Order fixes the order tags are written in.
FIELDS = {
    "id": "id",
    "name": "name",
    "category": "cat",
    "notes": "note",
    "wishlist": "wish",
    "asset_class": "class",
    "target_dims": "dims",
    "asset": "asset",
    "filled_by": "actor",
}

_LIST_FIELDS = ("wishlist",)
_FLOAT_LIST_FIELDS = ("target_dims",)


def validate_id(pin_id: str) -> str:
    """Pin ids are lowercase slugs. Unreal's FName comparison is
    case-INSENSITIVE, so `Market-03` and `market-03` would silently be the
    same pin; lowercase-only makes that impossible rather than surprising."""
    pin_id = str(pin_id).strip()
    if not _ID_RE.match(pin_id):
        raise TeeError(
            "bad_pin_id",
            f"Pin id {pin_id!r} is not a valid id.",
            fix="Use a lowercase slug of 1-48 chars from a-z 0-9 . _ - "
            "(e.g. 'market-03'). Ids are lowercase because the editor "
            "compares actor tags case-insensitively.",
        )
    return pin_id


def _clean(value: Any, field: str) -> str:
    text = str(value).replace("\n", " ").strip()
    if field in _LIST_FIELDS or field in _FLOAT_LIST_FIELDS:
        return text
    if LIST_SEP in text:
        raise TeeError(
            "bad_pin_field",
            f"Pin {field} may not contain {LIST_SEP!r}.",
            fix=f"{LIST_SEP!r} separates list entries inside a tag; drop it from the text.",
        )
    return text


def encode_tags(namespace: str, pin: dict[str, Any]) -> list[str]:
    """Render a pin dict as the full tag list for its actor."""
    tags = [namespace]
    for field, suffix in FIELDS.items():
        value = pin.get(field)
        if value is None or value == "" or value == []:
            continue
        if field in _LIST_FIELDS:
            parts = [_clean(v, field) for v in value]
            for part in parts:
                if LIST_SEP in part:
                    raise TeeError(
                        "bad_pin_field",
                        f"Wishlist term {part!r} may not contain {LIST_SEP!r}.",
                        fix="Terms are separated by that character inside one tag.",
                    )
            text = LIST_SEP.join(p for p in parts if p)
        elif field in _FLOAT_LIST_FIELDS:
            text = LIST_SEP.join(f"{float(v):g}" for v in value)
        else:
            text = _clean(value, field)
        if text:
            tags.append(f"{namespace}_{suffix}:{text}")
    return tags


def decode_tags(namespace: str, tags: list[str]) -> dict[str, Any] | None:
    """Read a pin back out of an actor's tags, or None if it is not a pin."""
    tags = [str(t) for t in tags]
    if namespace not in tags:
        return None
    by_suffix = {suffix: field for field, suffix in FIELDS.items()}
    out: dict[str, Any] = {"wishlist": [], "extra_tags": []}
    prefix = namespace + "_"
    for tag in tags:
        if tag == namespace:
            continue
        if not tag.startswith(prefix) or ":" not in tag:
            out["extra_tags"].append(tag)
            continue
        suffix, value = tag[len(prefix) :].split(":", 1)
        field = by_suffix.get(suffix)
        if field is None:
            out["extra_tags"].append(tag)
        elif field in _LIST_FIELDS:
            out[field] = [v for v in value.split(LIST_SEP) if v]
        elif field in _FLOAT_LIST_FIELDS:
            out[field] = [float(v) for v in value.split(LIST_SEP) if v]
        else:
            out[field] = value
    if not out.get("extra_tags"):
        out.pop("extra_tags")
    return out


def merge(existing: dict[str, Any] | None, updates: dict[str, Any]) -> dict[str, Any]:
    """Upsert semantics: fields not mentioned in `updates` keep their value.
    An explicit empty string / empty list clears a field."""
    pin = dict(existing or {})
    pin.pop("extra_tags", None)
    for field in FIELDS:
        if field in updates and updates[field] is not None:
            pin[field] = updates[field]
    return pin
