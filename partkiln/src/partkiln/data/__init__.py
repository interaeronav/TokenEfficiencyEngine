"""The standards data partkiln ships, and the one door to it.

Every table here is a licence question before it is a lookup: the obvious
sources for fastener dimensions (FreeCAD's Fasteners workbench, BOLTS, the
encyclopedia tables) are GPL or share-alike and never vendored, so the CSVs
are bd_warehouse's Apache-2.0 files and one table DERIVED from threadlib's
BSD-3 thread table. `manifest.json` names the source, licence and retrieval
date of every file, and `load_table` refuses a file whose entry lacks any of
the three - the D1 rule that a table with no paper trail is a guess, not a
standard.

Nothing here imports OCP, tee or numpy: `import partkiln` must work on a
machine that has none of them.
"""

from __future__ import annotations

import csv
import json
from functools import cache
from importlib import resources
from typing import Any

from partkiln.document import CommandError

REQUIRED_PROVENANCE = ("source", "licence", "retrieved")


class DataError(CommandError):
    """A data file that cannot be served: missing, or missing its provenance.

    A `CommandError` (the lane's one error type) so the adapter's
    `except CommandError` catches it; D8's `pk_not_served` is its code.
    """

    def __init__(self, message: str, *, code: str = "pk_not_served") -> None:
        super().__init__(message, code=code)


def _root():
    return resources.files("partkiln.data")


@cache
def manifest() -> dict[str, Any]:
    """The whole manifest, parsed once; `files` maps filename to its entry."""
    text = _root().joinpath("manifest.json").read_text(encoding="utf-8")
    return json.loads(text)


def provenance(name: str) -> dict[str, Any]:
    """The manifest entry for one shipped file.

    Refuses when the manifest has no entry or the entry lacks source, licence
    or retrieved - the loader is the enforcement point, so a future session
    dropping a CSV in without a paper trail finds out at the first lookup, not
    in an audit.
    """
    files = manifest().get("files", {})
    entry = files.get(name)
    if entry is None:
        known = ", ".join(sorted(files))
        raise DataError(
            f"{name!r} has no entry in partkiln/data/manifest.json. "
            f"Add one with source, licence and retrieved before serving it. Listed: {known}."
        )
    missing = [key for key in REQUIRED_PROVENANCE if not entry.get(key)]
    if missing:
        raise DataError(
            f"{name!r} is in the manifest without {', '.join(missing)}. "
            "A table without its provenance is not served; fill the field(s) in "
            "partkiln/data/manifest.json."
        )
    return dict(entry)


def _coerce(raw: str) -> float | str:
    """Numeric cells become floats; everything else stays text.

    The bd_warehouse files pad some cells (' 0.234') and leave blanks where a
    standard does not table a size; a blank stays '' so a lookup can say
    "not tabled" rather than serve 0.0 as a dimension.
    """
    text = raw.strip()
    if text == "":
        return ""
    try:
        return float(text)
    except ValueError:
        return text


@cache
def _rows(name: str) -> tuple[dict[str, float | str], ...]:
    text = _root().joinpath(name).read_text(encoding="utf-8")
    reader = csv.DictReader(text.splitlines())
    rows = []
    for row in reader:
        # Header keys are stripped because the shipped iso4762.csv carries
        # bd_warehouse's trailing spaces ('iso4762:dk ') and the file is kept
        # verbatim by rule.
        rows.append({(k or "").strip(): _coerce(v or "") for k, v in row.items()})
    return tuple(rows)


def load_table(name: str) -> list[dict[str, float | str]]:
    """The rows of one shipped CSV as dicts, numeric cells as floats.

    Provenance is checked BEFORE the file is read, so a table without a
    manifest entry is never served even if the bytes are present.
    """
    provenance(name)
    try:
        rows = _rows(name)
    except FileNotFoundError as exc:
        raise DataError(
            f"{name!r} is in the manifest but the file is absent from partkiln/data. "
            "Restore it from the source URL in the manifest."
        ) from exc
    return [dict(row) for row in rows]


def load_json(name: str) -> dict[str, Any]:
    """A shipped JSON document (the material cards), provenance-checked the same way."""
    provenance(name)
    try:
        text = _root().joinpath(name).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise DataError(
            f"{name!r} is in the manifest but the file is absent from partkiln/data. "
            "Restore it from the source URL in the manifest."
        ) from exc
    return json.loads(text)


def shipped_files() -> list[str]:
    """Every CSV/JSON in the package directory except the manifest itself."""
    names = []
    for entry in _root().iterdir():
        if entry.name == "manifest.json" or not entry.is_file():
            continue
        if entry.name.endswith((".csv", ".json")):
            names.append(entry.name)
    return sorted(names)


__all__ = [
    "REQUIRED_PROVENANCE",
    "DataError",
    "load_json",
    "load_table",
    "manifest",
    "provenance",
    "shipped_files",
]
