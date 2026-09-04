"""Coaxial and equal-radius is not enough to call two walls one hole.

Found by the A66 verify pass, attacking defect A from its dangerous side: that
fix taught `hole_table` to merge coaxial equal-radius faces into one wall, so a
mirror-joined bore stops printing twice. It merged them unconditionally, and
two BLIND holes sunk from opposite faces of a thick plate look exactly like one
bore drilled through in one pass. Measured on the merge-everything code, a
30 mm plate with a d10 hole 5 mm deep from each face - 20 mm of solid left
standing between them - printed:

    1 row   d10 THRU     "Ø10 THRU"

A shop reading that sheet drills through the wall. What decides is the METAL:
`brep.holes.material_between` classifies the midpoint of the axial gap, so a
clevis (two ears, air between) stays one THRU hole and two blind holes stay two.

The second half of this file is the guarantee that came later, on 2026-09-04:
`pk_drawing` and `pk_check` must never give two different answers about one
part. They did - `checks/spec.py` was still counting concave cylindrical FACES
while the table had learned twice that a concave face is not a hole - so a
40 x 20 pocket with r5 corners and no holes at all passed a spec of four Ø10
holes beside a sheet that tabled none. Both now ask `brep.holes.hole_walls`,
and every case below asserts that the two answers are the same number.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

import partkiln.drawing  # noqa: F401 - registers `create drawing`
from partkiln.checks.spec import check_spec
from partkiln.document import Document
from partkiln.drawing.verbs import build_drawing

pytestmark = pytest.mark.brep


def _plate_drilled_from_both_faces(thickness: float, depth: float) -> Document:
    """A 100 x 60 x `thickness` plate with a coaxial d10 blind hole `depth`
    deep from the top face and another `depth` deep from the bottom."""
    doc = Document()
    for op in (
        {"op": "create", "kind": "part", "name": "p"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "b",
            "props": {"plane": "XY", "profile": [{"rect": [100, 60], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "b", "distance": thickness},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "t",
            "props": {
                "plane": "on:body.end",
                "profile": [{"circle": 10, "at": [50, 30], "tag": "a"}],
            },
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "top",
            "props": {"sketch": "t", "distance": depth, "mode": "cut"},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "u",
            "props": {"plane": "XY", "profile": [{"circle": 10, "at": [50, 30], "tag": "b"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "bot",
            "props": {"sketch": "u", "distance": depth, "mode": "cut", "direction": "+"},
        },
    ):
        doc.apply(op)
    return doc


def _rows(doc: Document, of: str) -> list[dict[str, Any]]:
    drawing = build_drawing(
        doc,
        "t",
        {"of": of, "sheet": "A1L", "views": [{"name": "v", "dir": "top"}], "hole_table": True},
    )
    return list(drawing.holes)


@pytest.mark.parametrize(("thickness", "depth"), [(20.0, 5.0), (30.0, 5.0), (40.0, 8.0)])
def test_two_blind_holes_with_metal_between_them_are_two_rows(
    thickness: float, depth: float
) -> None:
    doc = _plate_drilled_from_both_faces(thickness, depth)
    # The metal really is there: only two blind holes' worth came out.
    removed = 100.0 * 60.0 * thickness - doc.parts["p"].volume()
    assert removed == pytest.approx(2.0 * math.pi * 25.0 * depth, abs=1e-3)

    rows = _rows(doc, "p")
    assert len(rows) == 2, rows
    assert {r["depth"] for r in rows} == {f"{depth:g}"}
    assert {r["dia_mm"] for r in rows} == {10.0}
    assert "THRU" not in {r["depth"] for r in rows}


def test_two_blind_holes_that_meet_are_still_one_THRU_row() -> None:
    """The case defect A fixed, unchanged: 5 + 5 through a 10 mm plate."""
    doc = _plate_drilled_from_both_faces(10.0, 5.0)
    rows = _rows(doc, "p")
    assert len(rows) == 1, rows
    assert rows[0]["dia_mm"] == 10.0 and rows[0]["depth"] == "THRU"


def test_a_clevis_drilled_through_both_ears_is_one_THRU_row() -> None:
    """AIR between the two walls, not metal: one hole drilled in one pass.

    A C-section 40 deep whose two 10 mm ears sit at z 0-10 and z 20-30, with a
    d10 hole down Z through both. The bore arrives as two cylindrical faces
    30 mm apart along its own axis - the same shape as the two blind holes
    above - and the classification of the gap is the whole difference.
    """
    doc = Document()
    for op in (
        {"op": "create", "kind": "part", "name": "clev"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "u",
            "props": {
                "plane": "YZ",
                "profile": [
                    {
                        "poly": [
                            [0, 0],
                            [40, 0],
                            [40, 10],
                            [10, 10],
                            [10, 20],
                            [40, 20],
                            [40, 30],
                            [0, 30],
                        ],
                        "tag": "u",
                    }
                ],
            },
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "u", "distance": 40},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "h",
            "props": {"plane": "XY", "profile": [{"circle": 10, "at": [20, 25], "tag": "pin"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "pin",
            "props": {"sketch": "h", "distance": "through", "mode": "cut"},
        },
    ):
        doc.apply(op)
    inv = doc.parts["clev"].inventory()
    assert sum(1 for f in inv.faces if f.surface_type == "cylinder") == 2  # two walls, one bore

    rows = _rows(doc, "clev")
    assert len(rows) == 1, rows
    assert rows[0]["dia_mm"] == 10.0 and rows[0]["depth"] == "THRU"


def _pocket_with_r5_corners() -> Document:
    """A 100 x 60 x 10 plate with a 40 x 20 x 5 pocket whose corners are r5.

    Four CONCAVE d10 cylindrical faces and NOT ONE HOLE - the part both the
    empty-table note and the `holes` defect were found on.
    """
    doc = Document()
    for op in (
        {"op": "create", "kind": "part", "name": "p"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "b",
            "props": {"plane": "XY", "profile": [{"rect": [100, 60], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "b", "distance": 10},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "k",
            "props": {
                "plane": "on:body.end",
                "profile": [{"rect": [40, 20], "at": [30, 20], "tag": "k"}],
            },
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "pk",
            "props": {"sketch": "k", "distance": 5, "mode": "cut"},
        },
        {
            "op": "create",
            "kind": "fillet",
            "name": "fr",
            "props": {"edges": "pk:edges(dir=Z)", "r": 5},
        },
    ):
        doc.apply(op)
    return doc


def _slotted_plate() -> Document:
    """A 100 x 60 x 10 plate with one 40 x 8 through slot, and nothing else."""
    doc = Document()
    for op in (
        {"op": "create", "kind": "part", "name": "p"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "b",
            "props": {"plane": "XY", "profile": [{"rect": [100, 60], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "b", "distance": 10},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": [{"slot": [40, 8], "at": [50, 30], "tag": "a"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "slot",
            "props": {"sketch": "s", "distance": "through", "mode": "cut"},
        },
    ):
        doc.apply(op)
    return doc


def test_an_empty_hole_table_does_not_name_a_fix_that_cannot_work() -> None:
    """A filleted pocket IS viewed down its corner axes; "add a view along the
    holes" was the note, and no view would ever find one. Both silences now."""
    doc = _pocket_with_r5_corners()
    drawing = build_drawing(
        doc,
        "t",
        {"of": "p", "sheet": "A1L", "views": [{"name": "v", "dir": "top"}], "hole_table": True},
    )
    assert drawing.holes == []  # defect A: this printed 4x d10
    note = "".join(n for n in drawing.notes if n.startswith("hole table:"))
    assert "fillets and corner radii" in note
    assert note != "hole table: no view looks down a hole axis; add a view along the holes"


# ------------------------------------- the sheet and the check give ONE answer


def _tabled(doc: Document, of: str, dia: float) -> int:
    """How many HOLES of `dia` the sheet tables (a slot row is not a hole)."""
    return sum(1 for r in _rows(doc, of) if r.get("kind") != "slot" and r["dia_mm"] == dia)


def _counted(doc: Document, of: str, dia: float) -> int:
    """How many holes of `dia` `pk_check` counts.

    Read out of the violation an impossible limit raises: `check_spec` answers
    a verdict, not an inventory, and this is the only way the public surface
    can be asked for the number it counted.
    """
    result = check_spec(doc.parts[of].shape, {"holes": [{"dia": dia, "count": 999}]})
    (violation,) = result["violations"]
    return int(violation["got"])


def test_the_pocket_that_made_the_two_tools_disagree() -> None:
    """The defect, from the side that names it: a pocket with NO HOLES.

    Measured on the old `_rule_holes` (2026-09-04): `holes: [{dia: 10,
    count: 4}]` -> `pass` and `count: 0` -> `fail, "found 4"`, while
    `hole_table` on the same solid returned zero rows. One part, two tools,
    two answers.
    """
    doc = _pocket_with_r5_corners()
    shape = doc.parts["p"].shape
    assert _tabled(doc, "p", 10.0) == 0
    assert _counted(doc, "p", 10.0) == 0

    assert check_spec(shape, {"holes": [{"dia": 10, "count": 0}]})["verdict"] == "pass"
    bad = check_spec(shape, {"holes": [{"dia": 10, "count": 4}]})
    assert bad["verdict"] == "fail"
    (v,) = bad["violations"]
    assert v["got"] == 0 and v["limit"] == 4 and "found 0" in v["fix"]


@pytest.mark.parametrize(("thickness", "depth", "expected"), [(30.0, 5.0, 2), (10.0, 5.0, 1)])
def test_the_sheet_and_the_check_agree_on_the_blind_pair(
    thickness: float, depth: float, expected: int
) -> None:
    """Metal between them: two rows AND two counted. None: one row AND one."""
    doc = _plate_drilled_from_both_faces(thickness, depth)
    assert _tabled(doc, "p", 10.0) == expected
    assert _counted(doc, "p", 10.0) == expected


def test_the_sheet_and_the_check_agree_that_a_slot_is_not_two_holes() -> None:
    """The behaviour change, pinned from both ends.

    `holes` used to count 2 for this part and the sheet has printed one SLOT
    row since the day before. A slot is checked with `slots` now: same width,
    same length, read by the same `brep.holes.slot_size` the row prints.
    """
    doc = _slotted_plate()
    shape = doc.parts["p"].shape
    (row,) = _rows(doc, "p")
    assert row["kind"] == "slot" and row["dia_mm"] == 8.0 and row["length_mm"] == 40.0

    assert _tabled(doc, "p", 8.0) == 0
    assert _counted(doc, "p", 8.0) == 0
    assert check_spec(shape, {"holes": [{"dia": 8, "count": 0}]})["verdict"] == "pass"
    assert check_spec(shape, {"slots": [{"width": 8, "length": 40}]})["verdict"] == "pass"

    ends = check_spec(shape, {"holes": [{"dia": 8, "count": 2}]})
    (v,) = ends["violations"]
    assert v["got"] == 0 and "2 slot end(s) of d8" in v["fix"] and "slots rule" in v["fix"]


def test_the_sheet_and_the_check_agree_on_the_w1_bracket() -> None:
    """The part that found the original lie: five rows, and four Ø6.6 holes.

    The sheet's fifth row is the slot, which `holes` does not count and
    `slots` does - so the two tools describe the same five features without
    ever printing the same one twice.
    """
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:  # `examples/` sits beside `src/`
        sys.path.insert(0, str(root))
    from examples.bracket.model import OPS

    doc = Document()
    for op in OPS:
        doc.apply(op)
    shape = doc.parts["bracket"].shape

    rows = _rows(doc, "bracket")
    assert len(rows) == 5
    assert sum(1 for r in rows if r.get("kind") == "slot") == 1
    assert _tabled(doc, "bracket", 6.6) == 4
    assert _counted(doc, "bracket", 6.6) == 4
    assert _counted(doc, "bracket", 8.0) == 0  # the slot's ends, tabled as one slot

    assert (
        check_spec(
            shape, {"holes": [{"dia": 6.6, "count": 4}], "slots": [{"width": 8, "length": 40}]}
        )["verdict"]
        == "pass"
    )
