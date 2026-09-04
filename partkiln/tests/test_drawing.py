"""P5a acceptance for `partkiln.drawing`: views, dimensions and three writers.

Every number here was measured against OCP 7.9.3 / ezdxf 1.4.4 / fpdf2 2.8.8 on
2026-09-02 (A66 P0a row 8 and the P5a acceptance list). A number that needs
hand-editing is a defect, never a widened tolerance.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

import partkiln.drawing  # noqa: F401 - registers `create drawing` and the method
from partkiln.brep import fixtures, shapes
from partkiln.client import LocalKernel
from partkiln.document import CommandError, Document
from partkiln.drawing import dims as dims_mod
from partkiln.drawing import dxf, hlr, pdf, svg, views
from partkiln.drawing.verbs import build_drawing, write_files

pytestmark = pytest.mark.brep

SVG_NS = "{http://www.w3.org/2000/svg}"


# --------------------------------------------------------------------------- fixtures


def _f1_document() -> Document:
    """F1: a 100 x 60 x 10 plate with a d10 through hole at (50, 30)."""
    doc = Document(name="f1")
    doc.apply({"op": "create", "kind": "part", "name": "plate"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [100, 60]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "base", "distance": 10},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {"on": "body.end", "at": [[50, 30]], "dia": 10},
        }
    )
    return doc


@pytest.fixture(scope="module")
def f1() -> Document:
    return _f1_document()


@pytest.fixture(scope="module")
def f2_plate() -> Document:
    """An F2-style plate: 80 x 60 x 6 with 4 x M6 clearance holes cut to ISO 273."""
    doc = Document(name="f2")
    doc.apply({"op": "create", "kind": "part", "name": "bracket"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [80, 60]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "plate",
            "props": {"sketch": "base", "distance": 6},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {
                "on": "plate.end",
                "at": [[20, 30], [60, 30], [20, 50], [60, 50]],
                "std": "M6 clearance",
            },
        }
    )
    return doc


@pytest.fixture(scope="module")
def f5() -> Document:
    """F5: 220 x 220 x 12 with a 10 x 10 grid of d8 holes at pitch 20 from (20, 20)."""
    doc = Document(name="f5")
    doc.apply({"op": "create", "kind": "part", "name": "plate"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [220, 220]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "base", "distance": 12},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {
                "on": "body.end",
                "at": [[20 + 20 * i, 20 + 20 * j] for i in range(10) for j in range(10)],
                "dia": 8,
            },
        }
    )
    return doc


@pytest.fixture(scope="module")
def drafted() -> Document:
    """A 40 x 40 x 20 box with ONE side drafted 3 degrees about the base."""
    doc = Document(name="f4")
    doc.apply({"op": "create", "kind": "part", "name": "bx"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": [{"rect": [40, 40]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "s", "distance": 20},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "draft",
            "name": "d",
            "props": {"faces": "body.side.rect.1", "angle": 3, "neutral": "body.start"},
        }
    )
    return doc


@pytest.fixture(scope="module")
def f1_sheet(f1: Document) -> Any:
    return build_drawing(
        f1,
        "sheet1",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}, {"name": "front", "dir": "front"}],
            "dims": [
                {"name": "d1", "view": "top", "kind": "extent", "axis": "X"},
                {"name": "d2", "view": "top", "kind": "extent", "axis": "Y"},
                {"name": "d3", "view": "top", "kind": "dia", "of": "h.1"},
            ],
            "title": {"part": "PLATE-001", "rev": "A"},
        },
    )


# --------------------------------------------------------------------------- HLR


def test_f1_per_compound_counts_under_named_projectors() -> None:
    """The measured table (A66 P0a row 8), compound by compound, not in total."""
    f1 = fixtures.build_F1()
    front = hlr.project(f1, (0, -1, 0), (0, 0, 1))
    assert front.compounds["VCompound"] == 4
    assert front.compounds["HCompound"] == 9
    assert front.compounds["OutLineHCompound"] == 1
    assert (front.visible_edges, front.hidden_edges) == (4, 10)

    top = hlr.project(f1, (0, 0, 1), (0, 1, 0))
    assert (top.compounds["VCompound"], top.compounds["HCompound"]) == (5, 5)
    assert (top.visible_edges, top.hidden_edges) == (5, 5)

    right = hlr.project(f1, (1, 0, 0), (0, 0, 1))
    assert right.compounds["VCompound"] == 4
    assert right.compounds["HCompound"] == 10
    assert right.compounds["OutLineHCompound"] == 2
    assert (right.visible_edges, right.hidden_edges) == (4, 12)


def test_hlr_is_under_30_ms_per_view() -> None:
    """P5a: <= 30 ms per view. Measured 0.2-1.1 ms on F1 (M5 Max, 2026-09-02)."""
    f1 = fixtures.build_F1()
    hlr.project(f1, (0, -1, 0))  # warm the OCCT side once
    for direction, up in (((0, -1, 0), (0, 0, 1)), ((0, 0, 1), (0, 1, 0)), ((1, 0, 0), (0, 0, 1))):
        started = time.perf_counter()
        hlr.project(f1, direction, up)
        assert (time.perf_counter() - started) * 1000.0 <= 30.0


def test_w3_the_trap_fixture_needs_the_union_of_compounds() -> None:
    """The 12-hole / 96-fillet plate: the sharp compound alone is not the view.

    Measured: V 9 + Rg1LineV 17 (union 26) | H 91 + Rg1LineH 63 + OutLineH 36,
    22 ms. A writer that read `VCompound` alone would drop 17 of 26 visible
    edges, which is why the design is the union (hlr.py).
    """
    w3 = fixtures.build_W3()
    started = time.perf_counter()
    front = hlr.project(w3, (0, -1, 0), (0, 0, 1))
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert front.visible, "the 96-fillet plate must have a non-empty front view"
    assert front.visible_edges > front.compounds["VCompound"]
    assert front.compounds["Rg1LineVCompound"] > 0
    assert front.hidden_edges > front.compounds["HCompound"]
    assert elapsed_ms <= 100.0, f"W3 HLR took {elapsed_ms:.1f} ms (measured 20.7)"


# --------------------------------------------------------------------------- layout


def test_third_angle_puts_top_above_front_first_angle_below(f1: Document) -> None:
    spec = {
        "of": "plate",
        "sheet": "A3L",
        "views": [
            {"name": "front", "dir": "front"},
            {"name": "top", "dir": "top"},
            {"name": "right", "dir": "right"},
        ],
    }
    third = build_drawing(f1, "t", {**spec, "angle": "third"})
    front, top, right = third.view("front"), third.view("top"), third.view("right")
    assert top.sheet_bbox()[1] > front.sheet_bbox()[3], "third angle: top ABOVE front"
    assert right.sheet_bbox()[0] > front.sheet_bbox()[2], "third angle: right to the RIGHT"

    first = build_drawing(f1, "f", {**spec, "angle": "first"})
    front, top, right = first.view("front"), first.view("top"), first.view("right")
    assert top.sheet_bbox()[3] < front.sheet_bbox()[1], "first angle: top BELOW front"
    assert right.sheet_bbox()[2] < front.sheet_bbox()[0], "first angle: right to the LEFT"


def test_the_angle_default_follows_the_standard(f1: Document) -> None:
    spec = {"of": "plate", "sheet": "A3L", "views": [{"name": "front", "dir": "front"}]}
    assert build_drawing(f1, "a", {**spec, "standard": "ISO"}).angle == "first"
    assert build_drawing(f1, "b", {**spec, "standard": "DIN"}).angle == "first"
    assert build_drawing(f1, "c", {**spec, "standard": "ANSI"}).angle == "third"
    assert views.angle_for("ISO") == "first" and views.angle_for("ANSI") == "third"
    # An explicit angle wins over the standard's default.
    assert build_drawing(f1, "d", {**spec, "standard": "ISO", "angle": "third"}).angle == "third"


def test_a_block_that_does_not_fit_the_sheet_is_refused(f5: Document) -> None:
    with pytest.raises(CommandError) as excinfo:
        build_drawing(
            f5,
            "big",
            {
                "of": "plate",
                "sheet": "A4L",
                "views": [
                    {"name": "front", "dir": "front"},
                    {"name": "top", "dir": "top"},
                    {"name": "right", "dir": "right"},
                ],
            },
        )
    assert excinfo.value.code == "pk_spec_conflict"
    assert "sheet:" in str(excinfo.value) and "scale:" in str(excinfo.value)


# --------------------------------------------------------------------------- sections


def test_section_at_x_50_hatches_500_mm2_in_two_faces(f1: Document) -> None:
    drawing = build_drawing(
        f1,
        "sec",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "front", "dir": "front"}, {"name": "cut", "dir": "section:x=50"}],
        },
    )
    view = drawing.view("cut")
    assert view.kind == "section"
    assert view.hatch_area_mm2 == 500.000
    assert view.hatch_faces == 2
    assert view.hatch, "a section view is hatched"
    assert view.summary()["hatch_area_mm2"] == 500.000


def test_a_stepped_shaft_sections_2700_mm2_lengthwise() -> None:
    """F3's shaft: d20x50 + d30x30 + d20x40 fused along z -> 49 480.084 mm3, and a
    plane through its axis cuts 1000 + 900 + 800 = 2 700.000 mm2."""
    shaft, _ = shapes.unify(
        shapes.fuse(
            [
                shapes.cylinder(10, 50, (0, 0, 0)),
                shapes.cylinder(15, 30, (0, 0, 50)),
                shapes.cylinder(10, 40, (0, 0, 80)),
            ]
        ).shape
    )
    assert round(shapes.volume(shaft), 3) == 49480.084
    body, faces = hlr.section_body(shaft, (0, 0, 0), (0, 1, 0))
    assert len(faces) == 1
    assert round(sum(f.area for f in faces), 3) == 2700.000
    assert hlr.project(body, (0, 1, 0), (0, 0, 1)).visible


def test_a_section_plane_outside_the_body_is_refused(f1: Document) -> None:
    part = f1.parts["plate"]
    with pytest.raises(CommandError) as excinfo:
        hlr.section_body(part.shape, (500, 0, 0), (1, 0, 0))
    assert excinfo.value.code == "pk_no_effect"
    assert "bbox" in str(excinfo.value) and "Fix:" in str(excinfo.value)


# --------------------------------------------------------------------------- details


def test_a_detail_window_reports_its_own_scale_and_its_hole(f1: Document) -> None:
    drawing = build_drawing(
        f1,
        "det",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [
                {"name": "top", "dir": "top"},
                {"name": "d", "dir": {"detail": {"of": "top", "on": "h.1", "r": 10, "scale": 2}}},
            ],
            "dims": [{"name": "dia", "view": "d", "kind": "dia", "of": "h.1"}],
        },
    )
    detail = drawing.view("d")
    assert detail.kind == "detail"
    assert detail.scale == 2.0
    assert detail.summary()["scale"] == 2.0
    assert "2:1" in detail.label
    assert drawing.view("top").window is not None, "the source view carries the window circle"
    assert drawing.dims[0].value_mm == 10.000 and drawing.dims[0].agree


# --------------------------------------------------------------------------- dimensions


def test_extents_and_dia_are_read_back_from_the_model(f1_sheet: Any) -> None:
    by_name = {d.name: d for d in f1_sheet.dims}
    assert by_name["d1"].value_mm == 100.000
    assert by_name["d2"].value_mm == 60.000
    assert by_name["d3"].value_mm == 10.000
    for dim in f1_sheet.dims:
        assert dim.agree, f"{dim.name}: model {dim.value_mm} vs drawn {dim.projected_mm}"
        assert dim.projected_mm == pytest.approx(dim.value_mm, abs=dims_mod.AGREE_TOL_MM)
    assert by_name["d3"].text == "Ø10"


def test_a_typed_dimension_value_is_refused(f1: Document) -> None:
    """Law 15: a drawing dimension is read back from the model, never typed."""
    with pytest.raises(CommandError) as excinfo:
        build_drawing(
            f1,
            "typed",
            {
                "of": "plate",
                "sheet": "A3L",
                "views": [{"name": "top", "dir": "top"}],
                "dims": [{"name": "d", "view": "top", "kind": "extent", "axis": "X", "value": 99}],
            },
        )
    assert excinfo.value.code == "pk_spec_conflict"
    assert "Law 15" in str(excinfo.value)


def test_distance_between_two_holes(f2_plate: Document) -> None:
    drawing = build_drawing(
        f2_plate,
        "dist",
        {
            "of": "bracket",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "dims": [
                {"name": "x", "view": "top", "kind": "dist", "a": "h.1", "b": "h.2", "axis": "X"},
                {"name": "y", "view": "top", "kind": "dist", "a": "h.1", "b": "h.3", "axis": "Y"},
            ],
        },
    )
    by_name = {d.name: d for d in drawing.dims}
    assert by_name["x"].value_mm == 40.000 and by_name["x"].agree
    assert by_name["y"].value_mm == 20.000 and by_name["y"].agree
    # The projected centre came from the circle the sheet actually drew.
    assert by_name["x"].projected_from == "arc"


def test_an_angular_dimension_reads_3_degrees_on_a_drafted_face(drafted: Document) -> None:
    drawing = build_drawing(
        drafted,
        "ang",
        {
            "of": "bx",
            "sheet": "A3L",
            "views": [{"name": "front", "dir": "front"}],
            "dims": [
                {
                    "name": "a1",
                    "view": "front",
                    "kind": "angle",
                    "a": "body.side.rect.1",
                    "b": "body.side.rect.3",
                }
            ],
        },
    )
    dim = drawing.dims[0]
    assert round(dim.value_mm, 3) == 3.000
    assert dim.agree and dim.text == "3°"
    assert dim.row()["angle_deg"] == 3.000


def test_a_chamfer_dimension_reads_its_leg_and_angle(f1: Document) -> None:
    doc = _f1_document()
    doc.apply(
        {
            "op": "create",
            "kind": "chamfer",
            "name": "c1",
            "props": {"edges": "body:edges(of=end, loop=outer)", "d": 2},
        }
    )
    part = doc.parts["plate"]
    face = next(n for n in sorted(part.inventory().aliases) if n.startswith("c1."))
    drawing = build_drawing(
        doc,
        "cham",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "front", "dir": "front"}],
            "dims": [{"name": "c", "view": "front", "kind": "chamfer", "of": face}],
        },
    )
    dim = drawing.dims[0]
    assert round(dim.value_mm, 3) == 2.000
    assert dim.row()["angle_deg"] == 45.000
    assert dim.text.startswith("2 ")
    del f1


def test_a_baseline_chain_steps_20_to_200_on_f5(f5: Document) -> None:
    drawing = build_drawing(
        f5,
        "chain",
        {
            "of": "plate",
            "sheet": "A1L",
            "views": [{"name": "top", "dir": "top"}],
            "dims": [
                {
                    "name": "b",
                    "view": "top",
                    "kind": "baseline",
                    "axis": "X",
                    "of": [f"h.{10 * i + 1}" for i in range(10)],
                },
                {
                    "name": "o",
                    "view": "top",
                    "kind": "ordinate",
                    "axis": "X",
                    "of": [f"h.{10 * i + 1}" for i in range(10)],
                },
            ],
        },
    )
    baseline, ordinate = drawing.dims[0], drawing.dims[1]
    expected = [20.0 * (i + 1) for i in range(10)]
    assert [round(v, 3) for v in baseline.values_mm] == expected
    assert [round(v, 3) for v in ordinate.values_mm] == expected
    assert baseline.value_mm == 200.000 and baseline.agree
    assert baseline.row()["from"] == "plate datum"


# --------------------------------------------------------------------------- tables


def test_the_hole_table_has_one_row_per_hole_on_f5(f5: Document) -> None:
    drawing = build_drawing(
        f5,
        "table",
        {
            "of": "plate",
            "sheet": "A1L",
            "views": [{"name": "top", "dir": "top"}],
            "hole_table": True,
        },
    )
    assert len(drawing.holes) == 100
    assert drawing.summary()["holes"] == 100
    assert {r["dia_mm"] for r in drawing.holes} == {8.0}
    assert {r["depth"] for r in drawing.holes} == {"THRU"}
    assert (drawing.holes[0]["x"], drawing.holes[0]["y"]) == (20.0, 20.0)
    assert drawing.notes == ["100\u00d7 \u00d88 THRU"]  # 100x d8 THRU, in drawing symbols
    # The picture is cut, the data never is (rule 1: compact by default).
    assert drawing.holes_shown == 26 and len(drawing.holes) == 100


def test_a_corner_fillet_is_not_a_hole(f2_plate: Document) -> None:
    """A convex cylinder is a fillet, and a fillet must never reach the sheet.

    Radius and axis alone cannot tell a hole from a corner fillet - they are
    the same surface with the material on opposite sides. Until 2026-09-04 the
    hole table took every cylinder whose axis faced the view, so filleting this
    plate's four corners at r3.3 added `4x d6.6 THRU` rows indistinguishable
    from its four real M6 clearance holes, and the note said eight. A shop
    reading that sheet drills four holes into thin air.
    """
    doc = Document.replay(f2_plate.script())  # module-scoped fixture: never mutate it
    doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "corners",
            "props": {"edges": "plate:edges(dir=Z)", "r": 3.3},  # r3.3 -> d6.6, as the holes
        }
    )
    drawing = build_drawing(
        doc,
        "fillets",
        {
            "of": "bracket",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "hole_table": True,
        },
    )
    assert len(drawing.holes) == 4, drawing.holes  # the holes, not the fillets
    assert drawing.notes == ["4\u00d7 \u00d86.6 THRU (M6 clearance, ISO 273 medium)"]
    # ... and the fillets really are there, at the very radius that fooled it.
    inv = doc.parts["bracket"].inventory()
    assert sum(1 for f in inv.faces if f.surface_type == "cylinder") == 8


def test_the_hole_note_cites_the_standard_the_hole_was_cut_to(f2_plate: Document) -> None:
    drawing = build_drawing(
        f2_plate,
        "note",
        {
            "of": "bracket",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "hole_table": True,
            "dims": [{"name": "d", "view": "top", "kind": "dia", "of": "h.1", "count": 4}],
        },
    )
    assert drawing.notes == ["4\u00d7 \u00d86.6 THRU (M6 clearance, ISO 273 medium)"]
    assert len(drawing.holes) == 4
    assert drawing.dims[0].value_mm == 6.600 and drawing.dims[0].agree
    assert drawing.dims[0].text == "4\u00d7 \u00d86.6"


# ------------------------------------------------------- a slot is one row, not two


def _slot_plate(
    angle: float | None = None,
    length: float = 40.0,
    width: float = 8.0,
    depth: float | str = "through",
) -> Document:
    """A 120 x 80 x 10 plate with one slot at its centre - W1's slot, without
    the fillets and the clearance holes that surround it there."""
    profile: dict[str, Any] = {"slot": [length, width], "at": [60, 40], "tag": "s"}
    if angle is not None:
        profile["angle"] = angle
    cut: dict[str, Any] = {"sketch": "cut", "distance": depth, "mode": "cut"}
    if depth != "through":
        cut["direction"] = "-"  # into the plate from its top face
    doc = Document(name="slotted")
    doc.apply({"op": "create", "kind": "part", "name": "plate"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [120, 80]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "base", "distance": 10},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "cut",
            "props": {"plane": "on:body.end", "profile": [profile]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "slot",
            "props": cut,
        }
    )
    return doc


def _hole_sheet(doc: Document, name: str = "s", of: str = "plate") -> Any:
    return build_drawing(
        doc,
        name,
        {
            "of": of,
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "hole_table": True,
        },
    )


def test_a_slot_tables_as_one_slot_and_not_as_two_holes() -> None:
    """Two ends walled together tangentially are one feature on the sheet.

    Both end cylinders are genuine concave cuts, so `2x d8 THRU` was never a
    false number - but it is not what a shop cuts. It sends a reader looking
    for two holes 32 mm apart (the CENTRE distance) where the model has a
    40 mm slot, and it prints no length at all. Every number in the merged row
    is read from the model: the width is twice the analytic radius and the
    length is the axis-to-axis distance plus one diameter.
    """
    doc = _slot_plate()
    drawing = _hole_sheet(doc)
    assert len(drawing.holes) == 1, drawing.holes
    row = drawing.holes[0]
    assert row["kind"] == "slot"
    assert row["dia_mm"] == 8.000  # the width: 2r, measured
    assert row["length_mm"] == 40.000  # centre distance 32 + one diameter
    assert (row["x"], row["y"]) == (60.0, 40.0)
    assert row["angle_deg"] == 0.0 and row["depth"] == "THRU"
    assert drawing.notes == ["40 \u00d7 8 SLOT THRU"]
    # The centre is the AXIS, never the face centroid: a slot end is a HALF
    # cylinder whose surface centroid sits 2r/pi = 2.546 mm off its own axis,
    # which would read the 40 mm slot as 34.907.
    inv = doc.parts["plate"].inventory()
    ends = [f for f in inv.faces if f.surface_type == "cylinder" and f.radius == 4.0]
    assert len(ends) == 2
    assert round(abs(ends[1].centroid[0] - ends[0].centroid[0]), 3) == 37.093


def test_two_holes_that_share_a_radius_are_not_a_slot() -> None:
    """The tangent WALL is the test, never the radius.

    These two d8 holes sit exactly 40 mm apart - the overall length of the W1
    slot - and share the plate's top and bottom faces. Nothing joins them but
    air. A merge here would print `40 x 8 SLOT THRU` for a part with no slot
    in it, so the pair must stay two rows.
    """
    doc = Document(name="pair")
    doc.apply({"op": "create", "kind": "part", "name": "plate"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [120, 80]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "base", "distance": 10},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {"on": "body.end", "at": [[40, 40], [80, 40]], "dia": 8},
        }
    )
    drawing = _hole_sheet(doc)
    assert len(drawing.holes) == 2, drawing.holes
    assert all("kind" not in row for row in drawing.holes)
    assert [row["dia_mm"] for row in drawing.holes] == [8.0, 8.0]
    assert round(drawing.holes[1]["x"] - drawing.holes[0]["x"], 3) == 40.0
    assert drawing.notes == ["2\u00d7 \u00d88 THRU"]


def test_a_hole_beside_a_slot_of_its_own_diameter_stays_a_hole() -> None:
    """The sharpest negative: the same radius, in the same part, in the same cut.

    A d8 hole 80 mm from a 40 x 8 slot shares the slot's ends' radius exactly.
    Only the tangent walls tell them apart, so this is the case that would go
    wrong the moment the test slipped from topology back to geometry.
    """
    doc = Document(name="mixed")
    doc.apply({"op": "create", "kind": "part", "name": "plate"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [160, 80]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "base", "distance": 10},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "cut",
            "props": {
                "plane": "on:body.end",
                "profile": [
                    {"slot": [40, 8], "at": [40, 40], "tag": "s"},
                    {"circle": 8, "at": [120, 40], "tag": "c"},
                ],
            },
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "slot",
            "props": {"sketch": "cut", "distance": "through", "mode": "cut"},
        }
    )
    drawing = _hole_sheet(doc)
    assert [row.get("kind") for row in drawing.holes] == ["slot", None]
    assert [row["dia_mm"] for row in drawing.holes] == [8.0, 8.0]
    assert drawing.notes == ["\u00d88 THRU", "40 \u00d7 8 SLOT THRU"]


def test_a_blind_slot_prints_the_depth_it_was_cut_to() -> None:
    """A slot's depth is the hole table's own depth cell, unchanged: `THRU`
    when the cut spans the body, the measured span otherwise."""
    drawing = _hole_sheet(_slot_plate(depth=4))
    row = drawing.holes[0]
    assert row["kind"] == "slot" and row["depth"] == "4"
    assert drawing.notes == ["40 \u00d7 8 SLOT 4"]


def test_a_slot_reports_the_angle_it_is_drawn_at() -> None:
    """The angle is the long axis projected into THIS view, folded to [0, 180)."""
    drawing = _hole_sheet(_slot_plate(angle=30.0))
    row = drawing.holes[0]
    assert row["kind"] == "slot" and row["angle_deg"] == 30.0
    assert row["length_mm"] == 40.000 and row["dia_mm"] == 8.000
    assert (row["x"], row["y"]) == (60.0, 40.0)


def test_the_w1_bracket_tables_five_rows_four_holes_and_one_slot() -> None:
    """The gap this closes, on the part that found it.

    W1 tabled six rows for five features: four M6 clearance holes and the
    slot's two ends. The fillets had already been evicted (2026-09-04); the
    slot is the last row that named a feature by its halves.
    """
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:  # `examples/` sits beside `src/`, per test_examples.py
        sys.path.insert(0, str(root))
    from examples.bracket.model import OPS

    kernel = LocalKernel()
    kernel.apply(OPS)
    drawing = _hole_sheet(kernel.document, of="bracket")
    assert len(drawing.holes) == 5, drawing.holes
    slots = [r for r in drawing.holes if r.get("kind") == "slot"]
    assert len(slots) == 1
    assert slots[0]["dia_mm"] == 8.000 and slots[0]["length_mm"] == 40.000
    assert slots[0]["name"] == "slot.side.slot.a0+a1"
    assert drawing.notes == [
        "4\u00d7 \u00d86.6 THRU (M6 clearance, ISO 273 medium)",
        "40 \u00d7 8 SLOT THRU",
    ]


def test_the_slot_note_reaches_the_svg_the_dxf_and_the_pdf(tmp_path: Path) -> None:
    """A note nobody can read on the sheet is not a note."""
    drawing = _hole_sheet(_slot_plate())
    note = "40 \u00d7 8 SLOT THRU"
    assert note in svg.render(drawing)

    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.readfile(dxf.write(drawing, tmp_path / "s.dxf"))
    texts = [e.dxf.text for e in doc.modelspace() if e.dxftype() == "TEXT"]
    assert note in texts, texts
    assert "SLOT" in " ".join(texts) and "HOLE TABLE (1)" in texts

    pytest.importorskip("fpdf", reason="partkiln[pdf] not installed")
    pypdf = pytest.importorskip("pypdf")
    text = pypdf.PdfReader(pdf.write(drawing, tmp_path / "s.pdf")).pages[0].extract_text()
    assert "SLOT" in text and "40" in text


# --------------------------------------- a corner radius is not a hole either


def _plate(name: str, width: float = 120.0, height: float = 80.0, thick: float = 10.0) -> Document:
    """A plain rectangular plate, the body every case below cuts into."""
    doc = Document(name=name)
    doc.apply({"op": "create", "kind": "part", "name": "plate"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [width, height]}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "base", "distance": thick},
        }
    )
    return doc


def _pocket_plate() -> Document:
    """A 120 x 80 x 10 plate with a 40 x 20 x 5 pocket whose corners are r5."""
    doc = _plate("pocketed")
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "cut",
            "props": {
                "plane": "on:body.end",
                "profile": [{"rect": [40, 20], "at": [60, 40], "tag": "p"}],
            },
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "pocket",
            "props": {"sketch": "cut", "distance": 5, "direction": "-", "mode": "cut"},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "fr",
            "props": {"edges": "pocket:edges(dir=Z)", "r": 5},
        }
    )
    return doc


def test_a_filleted_pocket_corner_is_not_a_hole() -> None:
    """The same lie wearing the other hat: a corner radius that IS concave.

    A convex fillet was evicted on 2026-09-04 because the material lay inside
    it. A POCKET's vertical corner radius is genuinely concave - the material
    really is outside it - so that test passes it honestly, and the table
    printed `4x d10 THRU` for this pocket: four holes a shop drills into a
    wall that has none, at a diameter (10) the part never mentions.

    What separates them is closure. A corner radius tangent to two walls
    meeting at interior angle t sweeps 180 - t degrees, 90 here and never
    more than 180; a drilled hole's wall goes the whole way round.
    """
    doc = _pocket_plate()
    drawing = _hole_sheet(doc)
    assert drawing.holes == [], drawing.holes
    assert not any("\u00d8" in note for note in drawing.notes), drawing.notes
    # The corners are really there, really concave, and really a quarter turn:
    # the row was dropped for the right reason, not because the pocket vanished.
    inv = doc.parts["plate"].inventory()
    corners = [f for f in inv.faces if f.surface_type == "cylinder"]
    assert len(corners) == 4
    assert all(f.radius == 5.0 for f in corners)
    assert all(shapes.is_concave_cylinder(f.shape) for f in corners)
    assert [round(shapes.cylinder_sweep_deg(f.shape), 6) for f in corners] == [90.0] * 4


def test_two_crossing_slots_print_no_phantom_holes() -> None:
    """Ends that cannot pair are still not holes.

    Crossing a 60 x 8 slot with a 40 x 8 one splits the walls each end would
    have paired through, so `_slot_pairs` honestly refuses to merge anything -
    and the four half-cylinder ends then printed `4x d8 THRU`. Each sweeps
    exactly half a turn, so none of them is a hole, and the sheet says
    nothing rather than saying something false.
    """
    doc = _plate("crossed")
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "cut",
            "props": {
                "plane": "on:body.end",
                "profile": [
                    {"slot": [60, 8], "at": [60, 40], "tag": "a"},
                    {"slot": [40, 8], "at": [60, 40], "angle": 90, "tag": "b"},
                ],
            },
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "cross",
            "props": {"sketch": "cut", "distance": "through", "mode": "cut"},
        }
    )
    drawing = _hole_sheet(doc)
    assert drawing.holes == [], drawing.holes
    inv = doc.parts["plate"].inventory()
    ends = [f for f in inv.faces if f.surface_type == "cylinder"]
    assert len(ends) == 4
    assert [round(shapes.cylinder_sweep_deg(f.shape), 6) for f in ends] == [180.0] * 4


def test_a_hole_that_reaches_the_inventory_as_two_faces_tables_once() -> None:
    """One hole, two half-cylinders, ONE row - and the row names both halves.

    Mirroring a half-round notch onto its own plane joins two half cylinders
    into a single d10 bore, and the table printed `2x d10 THRU`: one hole
    counted twice, the same species of lie as a fillet counted once. Faces
    sharing an axis and a radius are one wall, so their sweeps add.

    The sweep is read from the AREA and not from the parametric bounds
    because the bounds lie here: the first half reports u from 90 to 450
    degrees - a whole turn - on a face whose area is half of one.
    """
    doc = _plate("mirrored", width=60)
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "cut",
            "props": {
                "plane": "on:body.end",
                "profile": [{"circle": 10, "at": [60, 40], "tag": "c"}],
            },
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "notch",
            "props": {"sketch": "cut", "distance": "through", "mode": "cut"},
        }
    )
    doc.apply(
        {"op": "create", "kind": "mirror", "name": "m", "props": {"of": "plate", "plane": "x=60"}}
    )

    drawing = _hole_sheet(doc)
    assert len(drawing.holes) == 1, drawing.holes
    row = drawing.holes[0]
    assert row["dia_mm"] == 10.0 and row["depth"] == "THRU"
    assert (row["x"], row["y"]) == (60.0, 40.0)
    assert row["name"] == "notch.side.c+m.notch.side.c"
    assert drawing.notes == ["\u00d810 THRU"]

    inv = doc.parts["plate"].inventory()
    halves = [f for f in inv.faces if f.surface_type == "cylinder"]
    assert len(halves) == 2
    assert [round(shapes.cylinder_sweep_deg(f.shape), 6) for f in halves] == [180.0, 180.0]
    from OCP.BRepTools import BRepTools  # the bounds that lie, pinned as measured

    u0, u1, _, _ = BRepTools.UVBounds_s(halves[0].shape)
    assert round(math.degrees(u1 - u0), 6) == 360.0


def test_a_hole_cut_from_both_sides_is_one_row_and_reads_THRU() -> None:
    """One hole, two cuts, one row - and the depth is the UNION of the two.

    Drilling a 10 mm plate 5 mm from each side leaves two full-turn walls on
    one axis. The table printed them as two d10 holes 5 deep, and the deeper
    of the two is not the answer either: the hole goes through. The wall's
    reach is the union of its faces' reaches, read in the WALL's frame -
    the two cuts point their axes opposite ways, and unioning +Z against -Z
    would read this 10 mm plate as 15.
    """
    doc = _plate("both_sides", width=100, height=60)
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "up",
            "props": {"plane": "XY", "profile": [{"circle": 10, "at": [50, 30], "tag": "u"}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "lower",
            "props": {"sketch": "up", "distance": 5, "mode": "cut"},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "down",
            "props": {
                "plane": "on:body.end",
                "profile": [{"circle": 10, "at": [50, 30], "tag": "d"}],
            },
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "upper",
            "props": {"sketch": "down", "distance": 5, "direction": "-", "mode": "cut"},
        }
    )
    drawing = _hole_sheet(doc)
    assert len(drawing.holes) == 1, drawing.holes
    row = drawing.holes[0]
    assert row["dia_mm"] == 10.0 and row["depth"] == "THRU"
    assert row["name"] == "lower.side.u+upper.side.d"
    assert drawing.notes == ["\u00d810 THRU"]


def test_a_bore_a_keyway_has_cut_into_is_still_a_hole() -> None:
    """The threshold from below, on the case that would break if it rose.

    A d20 bore with a 3 mm keyway loses the arc between x = 48.5 and 51.5:
    2 * asin(1.5 / 10) = 17.254 degrees of it, leaving 342.746. That is a
    hole - a shop bores it - and it is why the closure test is 270 degrees
    and not 360: a corner radius cannot reach 180, so the margin above it
    buys room for real holes that a later feature has clipped.
    """
    doc = _plate("keyed", width=100, height=60)
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "cut",
            "props": {
                "plane": "on:body.end",
                "profile": [
                    {"circle": 20, "at": [50, 30], "tag": "b"},
                    {"rect": [3, 4], "at": [48.5, 38], "tag": "k"},
                ],
            },
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "bore",
            "props": {"sketch": "cut", "distance": "through", "mode": "cut"},
        }
    )
    drawing = _hole_sheet(doc)
    assert [row["dia_mm"] for row in drawing.holes] == [20.0]
    assert drawing.holes[0]["depth"] == "THRU"

    inv = doc.parts["plate"].inventory()
    (bore,) = [f for f in inv.faces if f.surface_type == "cylinder"]
    swept = shapes.cylinder_sweep_deg(bore.shape)
    assert round(swept, 3) == 342.746
    assert round(360.0 - 2.0 * math.degrees(math.asin(1.5 / 10.0)), 3) == 342.746  # the arithmetic
    assert swept > dims_mod.FULL_TURN_MIN_DEG


def test_a_through_a_blind_and_a_counterbored_hole_all_still_table() -> None:
    """The positives the closure test must not touch, counterbore included.

    A counterbore is two coaxial walls of DIFFERENT radii, so it tables under
    each of its own diameters (d16 x 4 deep and d10 through the rest) and the
    coaxial merge - which adds sweeps within one radius - never folds them
    into one row or counts either twice.
    """
    doc = _plate("drilled", width=100, height=60)
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "thru",
            "props": {"on": "body.end", "at": [[20, 30]], "dia": 10},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "bl",
            "props": {"on": "body.end", "at": [[50, 30]], "dia": 8, "depth": 5},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "cb",
            "props": {
                "on": "body.end",
                "at": [[80, 30]],
                "dia": 10,
                "seat": {"kind": "counterbore", "dia": 16, "depth": 4},
            },
        }
    )
    drawing = _hole_sheet(doc)
    assert [(r["name"], r["dia_mm"], r["depth"]) for r in drawing.holes] == [
        ("thru.1.wall", 10.0, "THRU"),
        ("bl.1.wall", 8.0, "5"),
        ("cb.1.seat.wall", 16.0, "4"),
        ("cb.1.wall", 10.0, "6"),
    ]


def test_the_parts_list_reads_the_bom_when_the_document_has_an_assembly() -> None:
    pytest.importorskip("partkiln.assembly.verbs")
    import partkiln.assembly.verbs  # noqa: F401 - registers `create component`

    doc = Document(name="f6")
    for name, side, height in (("block", 40, 20), ("pin", 10, 40)):
        doc.apply(
            {"op": "create", "kind": "part", "name": name, "props": {"material": "steel_s275"}}
        )
        profile = [{"rect": [side, side]}] if name == "block" else [{"circle": 10, "at": [20, 20]}]
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "name": f"s_{name}",
                "props": {"plane": "XY", "profile": profile},
            }
        )
        doc.apply(
            {
                "op": "create",
                "kind": "extrude",
                "name": f"b_{name}",
                "props": {"sketch": f"s_{name}", "distance": height, "part": name},
            }
        )
    doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "bh",
            "props": {"part": "block", "on": "b_block.end", "at": [[20, 20]], "dia": 10},
        }
    )
    doc.apply({"op": "create", "kind": "component", "name": "c1", "props": {"part": "block"}})
    doc.apply({"op": "create", "kind": "component", "name": "c2", "props": {"part": "pin"}})

    drawing = build_drawing(
        doc,
        "bom",
        {
            "of": "block",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "parts_list": True,
        },
    )
    assert len(drawing.parts) == 2
    assert [r["part"] for r in drawing.parts] == ["block", "pin"]
    assert [r["mass_g"] for r in drawing.parts] == [238.869, 24.662]


def test_a_parts_list_without_an_assembly_says_so(f1: Document) -> None:
    drawing = build_drawing(
        f1,
        "nobom",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "parts_list": True,
        },
    )
    assert drawing.parts == []
    assert any("no assembly" in note for note in drawing.notes)


def _priced_and_unpriced_document() -> Document:
    """Two parts in one assembly - one with a material, one without."""
    import partkiln.assembly.verbs  # noqa: F401 - registers `create component`

    doc = Document(name="bompart")
    for name, side, height, material in (
        ("block", 40, 20, "steel_s275"),
        ("spacer", 10, 5, None),
    ):
        doc.apply({"op": "create", "kind": "part", "name": name, "props": {"material": material}})
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "name": f"s_{name}",
                "props": {"plane": "XY", "profile": [{"rect": [side, side]}]},
            }
        )
        doc.apply(
            {
                "op": "create",
                "kind": "extrude",
                "name": f"b_{name}",
                "props": {"sketch": f"s_{name}", "distance": height, "part": name},
            }
        )
        doc.apply({"op": "create", "kind": "component", "props": {"part": name}})
    return doc


def _partial_sheet() -> Any:
    return build_drawing(
        _priced_and_unpriced_document(),
        "partial",
        {
            "of": "block",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "parts_list": True,
        },
    )


def test_an_unpriced_part_prints_a_placeholder_on_every_sheet(tmp_path: Path) -> None:
    """A mass the BOM cannot compute is `?` on the sheet, never `0.000` or `None`.

    The BOM answers `total_g: None` for a part with no material (defect 11),
    but the three writers each undid it in their own way - SVG's
    `float(x or 0.0)` printed `0.000` (a mass nobody measured) and DXF's and
    PDF's `.get("total_g", 0.0)` printed the literal string `None`, because
    the key EXISTS and is None. One shared formatter now writes the cell, and
    the heading says the total is partial.
    """
    ezdxf = pytest.importorskip("ezdxf")
    sheet = _partial_sheet()
    rows = {r["part"]: r for r in sheet.parts}
    assert rows["block"]["total_g"] == 251.2
    assert rows["spacer"]["mass_g"] is None and rows["spacer"]["total_g"] is None

    svg_texts = [(e.text or "") for e in ET.fromstring(svg.render(sheet)).iter(f"{SVG_NS}text")]
    assert "MASS PARTIAL" in " ".join(svg_texts)
    # The old SVG printed the spacer's unknown mass as the bare "0" its own
    # number formatter makes of 0.0 - so the zero is pinned out by value.
    assert "?" in svg_texts
    assert not {"0", "0.0", "0.000", "None"} & set(svg_texts)

    dxf_texts = [
        e.dxf.text
        for e in ezdxf.readfile(dxf.write(sheet, tmp_path / "p.dxf")).modelspace().query("TEXT")
    ]
    assert "?" in dxf_texts
    assert not {"0", "0.0", "0.000", "None"} & set(dxf_texts)
    assert any("MASS PARTIAL" in t for t in dxf_texts)

    pytest.importorskip("fpdf", reason="partkiln[pdf] not installed")
    pypdf = pytest.importorskip("pypdf")
    text = pypdf.PdfReader(pdf.write(sheet, tmp_path / "p.pdf")).pages[0].extract_text()
    assert "MASS PARTIAL" in text and "None" not in text

    heading, cells = svg.parts_table(sheet)
    assert heading == "PARTS LIST (2) - MASS PARTIAL, 1 OF 2 UNPRICED"
    assert [c[-1] for c in cells] == ["251.2", "?"]


def test_a_fully_priced_parts_list_says_nothing_about_partial() -> None:
    """The heading marks a partial total only when one is partial."""
    doc = _priced_and_unpriced_document()
    doc.apply({"op": "set", "id": "part:spacer", "props": {"material": "steel_s275"}})
    sheet = build_drawing(
        doc,
        "whole",
        {
            "of": "block",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "parts_list": True,
        },
    )
    heading, cells = svg.parts_table(sheet)
    assert heading == "PARTS LIST (2)"
    assert [c[-1] for c in cells] == ["251.2", "3.925"]


# --------------------------------------------------------------------------- SVG


def test_svg_parses_and_one_millimetre_is_one_user_unit(f1_sheet: Any) -> None:
    text = svg.render(f1_sheet)
    root = ET.fromstring(text)
    assert root.tag == f"{SVG_NS}svg"
    assert root.get("width") == "420mm" and root.get("height") == "297mm"
    assert root.get("viewBox") == "0 0 420 297"
    spans = {
        round(abs(float(e.get("x2")) - float(e.get("x1"))), 3) for e in root.iter(f"{SVG_NS}line")
    }
    assert 100.0 in spans, "the plate's 100 mm edge is 100 user units at 1:1"
    assert 60.0 in {
        round(abs(float(e.get("y2")) - float(e.get("y1"))), 3) for e in root.iter(f"{SVG_NS}line")
    }


def test_svg_dashes_and_counts_the_hidden_lines(f1_sheet: Any) -> None:
    text = svg.render(f1_sheet)
    root = ET.fromstring(text)
    hidden = [g for g in root.iter(f"{SVG_NS}g") if g.get("class") == "hidden"]
    drawn = sum(len(list(g)) for g in hidden)
    expected = sum(len(v.hidden) for v in f1_sheet.views)
    assert drawn == expected > 0
    assert ".hidden" in text and "stroke-dasharray" in text
    assert any(e.tag == f"{SVG_NS}circle" for e in root.iter()), "the hole is a native circle"


def test_svg_is_byte_identical_on_repeat(f1_sheet: Any, tmp_path: Path) -> None:
    assert svg.render(f1_sheet) == svg.render(f1_sheet)
    a = svg.write(f1_sheet, tmp_path / "a.svg")
    b = svg.write(f1_sheet, tmp_path / "b.svg")
    assert a.read_bytes() == b.read_bytes()


# --------------------------------------------------------------------------- DXF


def test_dxf_declares_millimetres_and_carries_real_dimensions(
    f1_sheet: Any, tmp_path: Path
) -> None:
    ezdxf = pytest.importorskip("ezdxf")
    path = dxf.write(f1_sheet, tmp_path / "sheet.dxf")
    doc = ezdxf.readfile(path)
    assert doc.header["$INSUNITS"] == 4  # millimetres
    names = {layer.dxf.name for layer in doc.layers}
    assert {"VISIBLE", "HIDDEN", "DIMS", "HATCH", "TITLE"} <= names

    measurements = sorted(d.get_measurement() for d in doc.modelspace().query("DIMENSION"))
    assert len(measurements) == 3
    # ezdxf's own linear_measurement rotates by the dimension angle, so the
    # VERTICAL 60 mm dim reads 59.999999999999986 (five ulp of ezdxf, not of us).
    assert measurements[0] == 10.0
    assert measurements[1] == pytest.approx(60.0, abs=1e-9)
    assert measurements[2] == 100.0
    vertical = next(
        d for d in doc.modelspace().query("DIMENSION") if abs(d.get_measurement() - 60.0) < 1e-9
    )
    assert abs(vertical.dxf.defpoint3.y - vertical.dxf.defpoint2.y) == 60.0

    assert doc.modelspace().query('*[layer=="VISIBLE"]')
    assert doc.modelspace().query('*[layer=="HIDDEN"]')


def test_dxf_is_byte_identical_on_repeat(f1_sheet: Any, tmp_path: Path) -> None:
    """ezdxf stamps a fresh GUID and a write timestamp; both are normalised."""
    a = dxf.write(f1_sheet, tmp_path / "a.dxf")
    b = dxf.write(f1_sheet, tmp_path / "b.dxf")
    assert a.read_bytes() == b.read_bytes()


def test_dxf_hatches_a_section_view(f1: Document, tmp_path: Path) -> None:
    ezdxf = pytest.importorskip("ezdxf")
    drawing = build_drawing(
        f1,
        "sec2",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "front", "dir": "front"}, {"name": "cut", "dir": "section:x=50"}],
        },
    )
    doc = ezdxf.readfile(dxf.write(drawing, tmp_path / "s.dxf"))
    assert len(doc.modelspace().query('*[layer=="HATCH"]')) == len(drawing.view("cut").hatch) > 0


# --------------------------------------------------------------------------- PDF


def test_pdf_page_is_the_sheet_and_its_text_is_real_text(f1_sheet: Any, tmp_path: Path) -> None:
    pytest.importorskip("fpdf", reason="partkiln[pdf] not installed")
    pypdf = pytest.importorskip("pypdf")
    path = pdf.write(f1_sheet, tmp_path / "sheet.pdf")
    page = pypdf.PdfReader(path).pages[0]
    # A3 landscape 420 x 297 mm at 72 pt / inch.
    assert round(float(page.mediabox.width), 2) == 1190.55
    assert round(float(page.mediabox.height), 2) == 841.89
    text = page.extract_text()
    assert "PLATE-001" in text and "REV A" in text and "SCALE 1:1" in text
    assert "100" in text and "Ø10" in text


def test_pdf_refuses_by_name_without_the_extra(
    f1_sheet: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "fpdf", None)
    with pytest.raises(CommandError) as excinfo:
        pdf.write(f1_sheet, tmp_path / "nope.pdf")
    assert excinfo.value.code == "pk_not_served"
    assert "partkiln[pdf]" in str(excinfo.value)
    assert "Fix:" in str(excinfo.value)


# --------------------------------------------------------------------------- the verbs


def test_create_drawing_stores_the_sheet_and_lists_its_rows(f1: Document) -> None:
    doc = _f1_document()
    result = doc.apply(
        {
            "op": "create",
            "kind": "drawing",
            "name": "sheet1",
            "props": {
                "of": "plate",
                "sheet": "A3L",
                "standard": "ANSI",
                "views": [{"name": "top", "dir": "top"}, {"name": "front", "dir": "front"}],
                "dims": [{"name": "d1", "view": "top", "kind": "extent", "axis": "X"}],
            },
        }
    )
    assert result["id"] == "dwg:sheet1"
    assert result["sheet"] == "A3L" and result["standard"] == "ANSI" and result["angle"] == "third"
    assert result["views"] == 2 and result["dims"] == 1
    assert result["view_rows"][0]["visible_edges"] == 5
    assert result["dimensions"] == [
        {"name": "d1", "value_mm": 100.0, "projected_mm": 100.0, "agree": True}
    ]
    assert "sheet1" in doc.drawings

    rows = doc.drawings["sheet1"].rows()
    assert [r["id"] for r in rows] == [
        "dwg:sheet1",
        "vw:top",
        "vw:front",
        "dim:d1",
    ]
    assert doc.summary()["drawings"] == 1

    # The same rows reach the document's own entity list (D7).
    listed = [r["id"] for r in doc.entities()]
    assert listed[-4:] == ["dwg:sheet1", "vw:top", "vw:front", "dim:d1"]
    assert doc.detail("vw:top")["visible_edges"] == 5
    assert doc.detail("dim:d1")["value_mm"] == 100.0
    assert doc.detail("dwg:sheet1")["dimensions"][0]["agree"] is True
    del f1


def test_a_drawing_replays_to_the_same_sheet() -> None:
    doc = _f1_document()
    doc.apply(
        {
            "op": "create",
            "kind": "drawing",
            "name": "sheet1",
            "props": {
                "of": "plate",
                "sheet": "A3L",
                "views": [{"name": "top", "dir": "top"}],
                "dims": [{"name": "d1", "view": "top", "kind": "extent", "axis": "X"}],
            },
        }
    )
    twin = Document.replay(doc.script())
    assert twin.fingerprint() == doc.fingerprint()
    assert svg.render(twin.drawings["sheet1"]) == svg.render(doc.drawings["sheet1"])


def test_pk_drawing_writes_the_files_and_answers_with_numbers(tmp_path: Path) -> None:
    pytest.importorskip("fpdf", reason="partkiln[pdf] not installed")
    kernel = LocalKernel(_f1_document())
    result = kernel.call(
        "drawing",
        {
            "name": "sheet1",
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}, {"name": "front", "dir": "front"}],
            "dims": [
                {"name": "d1", "view": "top", "kind": "extent", "axis": "X"},
                {"name": "d2", "view": "top", "kind": "extent", "axis": "Y"},
                {"name": "d3", "view": "top", "kind": "dia", "of": "h.1"},
            ],
            "hole_table": True,
            "formats": ["svg", "dxf", "pdf"],
            "out_dir": str(tmp_path),
        },
    )
    assert sorted(result["files"]) == ["dxf", "pdf", "svg"]
    for path in result["files"].values():
        assert Path(path).exists() and Path(path).stat().st_size > 0
    assert result["views"] == [
        {"name": "top", "dir": "top", "scale": 1.0, "visible_edges": 5, "hidden_edges": 5},
        {"name": "front", "dir": "front", "scale": 1.0, "visible_edges": 4, "hidden_edges": 10},
    ]
    assert [(d["name"], d["value_mm"], d["agree"]) for d in result["dimensions"]] == [
        ("d1", 100.0, True),
        ("d2", 60.0, True),
        ("d3", 10.0, True),
    ]
    assert result["hole_table"][0]["dia_mm"] == 10.0
    # A tool call writes files; it never lands in the script (Law 16).
    assert kernel.document.drawings == {}
    assert [c.op for c in kernel.document.history].count("create") == 4


def test_pk_drawing_needs_no_disk_for_the_numbers() -> None:
    kernel = LocalKernel(_f1_document())
    result = kernel.call(
        "drawing",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "dims": [{"name": "d1", "view": "top", "kind": "extent", "axis": "X"}],
        },
    )
    assert result["files"] == {}
    assert result["dimensions"][0]["value_mm"] == 100.0


# --------------------------------------------------------------------------- refusals


@pytest.mark.parametrize(
    ("props", "code", "needle"),
    [
        ({"of": "plate", "sheet": "A9Z", "views": []}, "pk_needs", "A4L"),
        ({"of": "nope", "views": []}, "pk_ref_unknown", "plate"),
        ({"of": "plate", "standard": "JIS", "views": []}, "pk_needs", "ISO"),
        ({"of": "plate", "angle": "second", "views": []}, "pk_needs", "'first'"),
        ({"of": "plate", "scale": "1:0", "views": []}, "pk_needs", "divides by zero"),
        (
            {"of": "plate", "views": [{"name": "v", "dir": "sideways"}]},
            "pk_needs",
            "front",
        ),
        (
            {"of": "plate", "views": [{"name": "v", "dir": {"detail": {"of": "v", "r": 5}}}]},
            "pk_ref_unknown",
            "declared before it",
        ),
        (
            {
                "of": "plate",
                "views": [
                    {"name": "top", "dir": "top"},
                    {"name": "d", "dir": {"detail": {"of": "top"}}},
                ],
            },
            "pk_needs",
            "needs r",
        ),
        (
            {
                "of": "plate",
                "views": [{"name": "top", "dir": "top"}],
                "dims": [{"name": "d", "view": "nope", "kind": "extent", "axis": "X"}],
            },
            "pk_ref_unknown",
            "no view",
        ),
        (
            {
                "of": "plate",
                "views": [{"name": "top", "dir": "top"}],
                "dims": [{"name": "d", "view": "top", "kind": "wobble"}],
            },
            "pk_bad_op",
            "extent",
        ),
        (
            {
                "of": "plate",
                "views": [{"name": "top", "dir": "top"}],
                "dims": [{"name": "d", "view": "top", "kind": "extent", "axis": "Q"}],
            },
            "pk_needs",
            "axis",
        ),
        (
            {
                "of": "plate",
                "views": [{"name": "top", "dir": "top"}],
                "dims": [{"name": "d", "view": "top", "kind": "dia", "of": "body.end"}],
            },
            "pk_ref_unknown",
            "cylinder",
        ),
    ],
)
def test_every_refusal_names_the_reason_and_the_fix(
    f1: Document, props: dict[str, Any], code: str, needle: str
) -> None:
    with pytest.raises(CommandError) as excinfo:
        build_drawing(f1, "bad", dict(props))
    assert excinfo.value.code == code
    assert needle in str(excinfo.value)


def test_an_unknown_format_lists_the_ones_that_work(f1_sheet: Any, tmp_path: Path) -> None:
    with pytest.raises(CommandError) as excinfo:
        write_files(f1_sheet, ["dwg"], tmp_path)
    assert excinfo.value.code == "pk_needs"
    assert "svg, dxf, pdf" in str(excinfo.value)


def test_an_auxiliary_view_looks_along_a_named_face_normal(drafted: Document) -> None:
    """`aux:<face ref>` puts the eye on the face's outward normal, so a drafted
    wall is seen square: its projected height is the wall itself, not the
    cosine-shortened one the front view draws."""
    drawing = build_drawing(
        drafted,
        "aux",
        {
            "of": "bx",
            "sheet": "A3L",
            "views": [
                {"name": "front", "dir": "front"},
                {"name": "a", "dir": "aux:body.side.rect.1"},
            ],
        },
    )
    aux = drawing.view("a")
    assert aux.kind == "aux"
    assert aux.label == "AUX body.side.rect.1"
    assert aux.summary()["of"] == "body.side.rect.1"
    # The drafted face normal is (0.9986, 0, -0.0523): the eye is on it.
    assert aux.frame.direction == pytest.approx((0.99863, 0.0, -0.05234), abs=1e-4)
    assert aux.visible_edges > 0


def test_an_iso_view_projects_the_body_pictorially(f1: Document) -> None:
    drawing = build_drawing(
        f1,
        "iso",
        {"of": "plate", "sheet": "A3L", "views": [{"name": "p", "dir": "iso"}]},
    )
    view = drawing.view("p")
    assert view.dir_token == "iso"
    assert view.visible_edges > 0
    width, height = view.size()
    assert width > 60.0 and height > 10.0, "an isometric view is taller than the plate"


def test_a_half_scale_sheet_halves_the_drawing_not_the_dimension(f1: Document) -> None:
    """The scale lives in the COORDINATES; the dimension value stays the model's."""
    full = build_drawing(
        f1,
        "full",
        {
            "of": "plate",
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}],
            "dims": [{"name": "d", "view": "top", "kind": "extent", "axis": "X"}],
        },
    )
    half = build_drawing(
        f1,
        "half",
        {
            "of": "plate",
            "sheet": "A3L",
            "scale": "1:2",
            "views": [{"name": "top", "dir": "top"}],
            "dims": [{"name": "d", "view": "top", "kind": "extent", "axis": "X"}],
        },
    )
    assert half.scale == 0.5
    assert half.summary()["scale"] == "1:2"
    assert half.view("top").size()[0] == pytest.approx(0.5 * full.view("top").size()[0])
    assert half.dims[0].value_mm == full.dims[0].value_mm == 100.000
    assert half.dims[0].agree
    assert "SCALE 1:2" in svg.render(half)


def test_an_up_vector_along_the_line_of_sight_is_refused() -> None:
    with pytest.raises(CommandError) as excinfo:
        hlr.view_frame((0, 0, 1), (0, 0, 1))
    assert excinfo.value.code == "pk_needs"
    assert "[0, 1, 0]" in str(excinfo.value)


# --------------------------------------------------------------------------- hygiene


def test_importing_the_drawing_package_costs_no_ocp() -> None:
    """D1: `import partkiln.drawing` must not pull in the 0.3-26 s OCP import."""
    src = Path(sys.modules["partkiln"].__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, partkiln.drawing; "
            "print('OCP' in sys.modules, 'ezdxf' in sys.modules, 'fpdf' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(src)},
        check=True,
    )
    assert proc.stdout.strip() == "False False False"
