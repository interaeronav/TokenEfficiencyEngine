"""What a drawing sheet IS, as data.

The critic reads this, not the rendered PDF. That is the whole reason the loop
can close: a finding names a field, the corrector edits that field, and the
sheet is drawn again from the corrected data. Critiquing pixels would let you
see a fault and not be able to fix it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Text:
    role: str  # title | subtitle | grid | dimension | note
    height_mm: float
    content: str = ""


@dataclass
class Line:
    role: str  # border | cut_primary | cut_secondary | beyond | fitting | hatch
    width_mm: float


@dataclass
class Marker:
    """A section or detail marker: a cut line on a plan pointing at a sheet."""

    tag: str  # "A", "B", ...
    target_sheet: str  # the sheet the section is drawn on
    drawn_on: str  # the sheet carrying the cut line
    direction_deg: float = 0.0


@dataclass
class Room:
    number: str
    name: str = ""
    area_m2: float | None = None


@dataclass
class View:
    kind: str  # ga_plan | ga_section | pictorial | ...
    name: str
    scale_denominator: int
    north_point: bool = False
    dimension_chains: list[str] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    levels: list[str] = field(default_factory=list)


@dataclass
class Revision:
    """One issue. The KB is explicit that a code alone is not enough: every
    revision needs a date, a one-line description and the initials of the
    author and the checker, listed in a table on the sheet."""

    code: str
    date: str
    description: str
    by: str = ""
    checked: str = ""


@dataclass
class TitleBlock:
    fields: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class Sheet:
    number: str
    title: str
    subtitle: str
    size: str = "A3"
    orientation: str = "landscape"
    views: list[View] = field(default_factory=list)
    texts: list[Text] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    markers: list[Marker] = field(default_factory=list)
    title_block: TitleBlock = field(default_factory=TitleBlock)
    revisions: list[Revision] = field(default_factory=list)
    level_datum: str = ""
    dimension_units: str = "mm"
    provenance: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def text(self, role: str) -> list[Text]:
        return [t for t in self.texts if t.role == role]


@dataclass
class DrawingSet:
    """A set, because some rules are only checkable across sheets.

    An orphan section marker is the obvious one: SK-02 saying 'cut lines shown
    on SK-01' is only a defect if SK-01 does not in fact show them, and no
    single sheet knows that.
    """

    sheets: list[Sheet] = field(default_factory=list)

    def by_number(self, number: str) -> Sheet | None:
        return next((s for s in self.sheets if s.number == number), None)
