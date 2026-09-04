"""A66 gap 7 — the vector block, and the units it refuses to leave implicit.

`pdf_compose` could write prose and pictures and not a single line, so a
partkiln drawing reached a PDF through partkiln's own optional fpdf2 extra
rather than through TEE's PDF lane. These tests pin the geometry the lane
now draws, and they measure it: a 100 mm line at 1:1 measures 100 mm, the
same line at 1:2 measures 50, and the mediabox is the sheet that was asked
for. A test that only asserted "the file got bigger" would prove nothing.

Everything here reads the WRITTEN file back - pdfplumber for positioned
geometry and text, pypdf for the mediabox and for the raw content-stream
operators - never the composer's own idea of what it drew.
"""

from __future__ import annotations

import math

import pytest

from tee import pdf
from tee.kernel.errors import TeeError

pdfplumber = pytest.importorskip("pdfplumber")
pypdf = pytest.importorskip("pypdf")
pytest.importorskip("fpdf")

PT_PER_MM = 72.0 / 25.4

# MEASURED, 2026-09-04, fpdf2 2.8.8: every coordinate reaches the content
# stream through "%.2f" of a POINT, so an endpoint can move by up to 0.005 pt
# = 0.0018 mm and a length by twice that. The 100 mm line below measures
# 100.0019 mm, not 100.0000. This tolerance is that rounding and nothing
# else - it is not a licence to be a hundredth of a millimetre out.
FPDF_ROUNDING_MM = 0.01


def mm(points: float) -> float:
    return points / PT_PER_MM


def _sheet(tmp_path, name="v.pdf", **spec):
    spec.setdefault("out", str(tmp_path / name))
    return pdf.compose(spec)


def _lines(path):
    with pdfplumber.open(str(path)) as doc:
        return list(doc.pages[0].lines)


def _stream(path) -> str:
    return pypdf.PdfReader(str(path)).pages[0].get_contents().get_data().decode("latin-1")


# -- the measurement that is the whole point --------------------------------


def test_a_100mm_line_measures_100mm_at_1_to_1(tmp_path):
    """The acceptance: a drawing whose lengths are not the lengths asked for
    is not a drawing, it is a picture."""
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "units": "mm",
                "origin": "bottom_left",
                "at": [10, 10],
                "items": [{"kind": "line", "from": [0, 0], "to": [100, 0]}],
            }
        ],
    )
    (line,) = _lines(tmp_path / "v.pdf")
    assert mm(line["x1"] - line["x0"]) == pytest.approx(100.0, abs=FPDF_ROUNDING_MM)
    # and it starts where it was told to, not merely with the right length
    assert mm(line["x0"]) == pytest.approx(10.0, abs=FPDF_ROUNDING_MM)
    # y up: 10 mm above the bottom of a 200 mm sheet is 190 mm from the top
    assert mm(line["top"]) == pytest.approx(190.0, abs=FPDF_ROUNDING_MM)


def test_the_same_line_at_1_to_2_measures_50_and_the_answer_says_so(tmp_path):
    """A sheet whose scale is implicit is a sheet that lies, so the scale is
    both applied and echoed."""
    result = _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "units": "mm",
                "origin": "bottom_left",
                "scale": "1:2",
                "at": [10, 10],
                "items": [{"kind": "line", "from": [0, 0], "to": [100, 0]}],
            }
        ],
    )
    (line,) = _lines(tmp_path / "v.pdf")
    assert mm(line["x1"] - line["x0"]) == pytest.approx(50.0, abs=FPDF_ROUNDING_MM)
    assert result["vector_frames"] == [
        {"units": "mm", "origin": "bottom_left", "scale": "1:2", "at_mm": [10.0, 10.0]}
    ]
    assert result["vector_items"] == 1


def test_an_enlargement_scale_reads_back_as_such(tmp_path):
    result = _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "scale": 2,
                "items": [{"kind": "line", "from": [0, 10], "to": [20, 10]}],
            }
        ],
    )
    (line,) = _lines(tmp_path / "v.pdf")
    assert mm(line["x1"] - line["x0"]) == pytest.approx(40.0, abs=FPDF_ROUNDING_MM)
    assert result["vector_frames"][0]["scale"] == "2:1"


@pytest.mark.parametrize(
    ("units", "length", "expect_mm"),
    [("mm", 100, 100.0), ("cm", 10, 100.0), ("in", 4, 101.6), ("pt", 288, 101.6)],
)
def test_every_unit_lands_in_millimetres(tmp_path, units, length, expect_mm):
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "units": units,
                "items": [{"kind": "line", "from": [0, 10], "to": [length, 10]}],
            }
        ],
    )
    (line,) = _lines(tmp_path / "v.pdf")
    assert mm(line["x1"] - line["x0"]) == pytest.approx(expect_mm, abs=FPDF_ROUNDING_MM)


def test_the_origin_choice_mirrors_y_and_nothing_else(tmp_path):
    """The same numbers in the two frames must land symmetrically about the
    middle of the sheet - that IS what choosing an origin means."""
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "origin": "top_left",
                "items": [{"kind": "line", "from": [0, 30], "to": [50, 30]}],
            },
            {
                "kind": "vector",
                "origin": "bottom_left",
                "items": [{"kind": "line", "from": [0, 30], "to": [50, 30]}],
            },
        ],
    )
    down, up = _lines(tmp_path / "v.pdf")
    assert mm(down["top"]) == pytest.approx(30.0, abs=FPDF_ROUNDING_MM)
    assert mm(up["top"]) == pytest.approx(170.0, abs=FPDF_ROUNDING_MM)
    assert mm(down["x0"]) == pytest.approx(mm(up["x0"]), abs=FPDF_ROUNDING_MM)


# -- the sheet itself -------------------------------------------------------


def test_the_mediabox_is_the_sheet_that_was_asked_for(tmp_path):
    _sheet(tmp_path, page="A3", orientation="landscape", blocks=[{"kind": "spacer", "mm": 1}])
    box = pypdf.PdfReader(str(tmp_path / "v.pdf")).pages[0].mediabox
    assert float(box.width) == pytest.approx(420.0 * PT_PER_MM, abs=0.01)
    assert float(box.height) == pytest.approx(297.0 * PT_PER_MM, abs=0.01)


def test_the_default_page_is_still_a4_portrait(tmp_path):
    """A66 added a page parameter; it must not have moved anyone's A4."""
    result = _sheet(tmp_path, blocks=[{"kind": "paragraph", "text": "unchanged"}])
    assert result["page_mm"] == [210.0, 297.0]
    box = pypdf.PdfReader(str(tmp_path / "v.pdf")).pages[0].mediabox
    assert float(box.width) == pytest.approx(595.28, abs=0.01)
    assert float(box.height) == pytest.approx(841.89, abs=0.01)


def test_an_explicit_page_size_is_taken_literally(tmp_path):
    result = _sheet(tmp_path, page=[123.0, 456.0], blocks=[{"kind": "spacer", "mm": 1}])
    assert result["page_mm"] == [123.0, 456.0]


def test_a_wide_table_uses_the_wide_sheet(tmp_path):
    """The flowing blocks were written against a hardcoded 180 mm content
    width. On an A3 sheet that would have left a third of the page empty."""
    _sheet(
        tmp_path,
        page="A3",
        blocks=[{"kind": "table", "rows": [["a", "b"]]}],
    )
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        right = max(r["x1"] for r in doc.pages[0].rects)
    assert mm(right) == pytest.approx(297.0 - 15.0, abs=0.5)


# -- what a mechanical sheet needs ------------------------------------------


def test_a_hidden_edge_is_dashed_and_a_visible_edge_is_not(tmp_path):
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "items": [
                    {"kind": "line", "from": [10, 10], "to": [90, 10], "width_mm": 0.5},
                    {"kind": "line", "from": [10, 20], "to": [90, 20], "dash": "hidden"},
                    {"kind": "line", "from": [10, 30], "to": [90, 30], "dash": [4, 2]},
                ],
            }
        ],
    )
    visible, hidden, custom = _lines(tmp_path / "v.pdf")
    assert hidden["dash"][0], "a hidden edge must be dashed"
    assert [round(mm(v), 2) for v in hidden["dash"][0]] == [2.5, 1.5]
    assert [round(mm(v), 2) for v in custom["dash"][0]] == [4.0, 2.0]
    # a line that was never dashed carries no dash entry at all: fpdf2 emits
    # the `d` operator only when the pattern changes
    assert not visible["dash"] or not visible["dash"][0], "a visible edge must be solid"
    # widths are PAPER millimetres, which is what a line width means
    assert mm(visible["linewidth"]) == pytest.approx(0.5, abs=0.01)
    assert mm(hidden["linewidth"]) == pytest.approx(0.25, abs=0.01)
    assert "d\n" in _stream(tmp_path / "v.pdf"), "no dash operator reached the stream"


def test_a_line_width_is_paper_millimetres_at_any_scale(tmp_path):
    """0.35 mm is 0.35 mm at 1:1 and at 1:50. If the scale touched it, a
    site plan would be drawn with a pencil the width of a wall."""
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "scale": "1:50",
                "width_mm": 0.35,
                "items": [{"kind": "line", "from": [0, 100], "to": [5000, 100]}],
            }
        ],
    )
    (line,) = _lines(tmp_path / "v.pdf")
    assert mm(line["linewidth"]) == pytest.approx(0.35, abs=0.01)
    assert mm(line["x1"] - line["x0"]) == pytest.approx(100.0, abs=FPDF_ROUNDING_MM)


def test_a_dimension_line_carries_two_arrowheads(tmp_path):
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "origin": "bottom_left",
                "items": [
                    {
                        "kind": "line",
                        "from": [20, 20],
                        "to": [120, 20],
                        "arrows": "both",
                        "arrow_mm": 3.0,
                    }
                ],
            }
        ],
    )
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        filled = [c for c in doc.pages[0].curves if c.get("fill")]
    assert len(filled) == 2, "an arrowhead at each end"
    tips = sorted(round(mm(c["x0"]), 1) for c in filled)
    # one head sits at x=20 pointing back, the other ends at x=120
    assert tips[0] == pytest.approx(20.0, abs=0.05)
    assert round(mm(max(c["x1"] for c in filled)), 1) == pytest.approx(120.0, abs=0.05)
    assert " f\n" in _stream(tmp_path / "v.pdf"), "no fill operator reached the stream"


def test_a_title_block_reads_back_at_the_positions_it_was_given(tmp_path):
    """Text at an exact point is half of a title block; the box is the other
    half. Both are asserted where they were put, not merely that they exist."""
    _sheet(
        tmp_path,
        page="A3",
        orientation="landscape",
        blocks=[
            {
                "kind": "vector",
                "origin": "bottom_left",
                "size_pt": 9,
                "items": [
                    {"kind": "rect", "at": [230, 10], "size": [180, 40], "width_mm": 0.5},
                    {"kind": "line", "from": [230, 30], "to": [410, 30]},
                    {"kind": "text", "at": [235, 35], "text": "BRACKET W1"},
                    {"kind": "text", "at": [235, 15], "text": "SCALE 1:2"},
                ],
            }
        ],
    )
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        page = doc.pages[0]
        words = {w["text"]: w for w in page.extract_words()}
        # a glyph's box hangs below its baseline by the descender, so the
        # baseline itself is read from the text matrix, which is exact
        baselines = {c["text"]: c["matrix"][5] for c in page.chars}
        (box,) = page.rects
    assert mm(box["x0"]) == pytest.approx(230.0, abs=FPDF_ROUNDING_MM)
    assert mm(box["top"]) == pytest.approx(297.0 - 50.0, abs=FPDF_ROUNDING_MM)
    assert mm(box["width"]) == pytest.approx(180.0, abs=FPDF_ROUNDING_MM)
    assert mm(box["height"]) == pytest.approx(40.0, abs=FPDF_ROUNDING_MM)
    assert set(words) == {"BRACKET", "W1", "SCALE", "1:2"}
    # the baseline is where it was asked for: 35 mm up the sheet
    assert mm(baselines["B"]) == pytest.approx(35.0, abs=FPDF_ROUNDING_MM)
    assert mm(words["BRACKET"]["x0"]) == pytest.approx(235.0, abs=0.2)
    assert mm(baselines["S"]) == pytest.approx(15.0, abs=FPDF_ROUNDING_MM)


def test_text_is_centred_on_the_point_when_asked(tmp_path):
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "items": [
                    {"kind": "text", "at": [100, 50], "text": "120", "align": "center"},
                    {"kind": "text", "at": [100, 80], "text": "120", "align": "left"},
                ],
            }
        ],
    )
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        centred, left = doc.pages[0].extract_words()
    width = mm(centred["x1"] - centred["x0"])
    assert mm(centred["x0"]) == pytest.approx(100.0 - width / 2, abs=0.2)
    assert mm(left["x0"]) == pytest.approx(100.0, abs=0.2)


def test_text_at_an_angle_is_rotated_in_the_blocks_own_frame(tmp_path):
    """A vertical dimension's text reads upwards. In a y-up frame +90 turns
    counter-clockwise on the paper; in a y-down frame the same +90 turns the
    other way, because the frame is what the angle is measured in."""
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "origin": "bottom_left",
                "items": [{"kind": "text", "at": [50, 50], "text": "A", "angle_deg": 90}],
            },
            {
                "kind": "vector",
                "origin": "top_left",
                "items": [{"kind": "text", "at": [150, 50], "text": "B", "angle_deg": 90}],
            },
        ],
    )
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        chars = {c["text"]: c for c in doc.pages[0].chars}
    assert chars["A"]["upright"] is False and chars["B"]["upright"] is False
    # the text matrices are each other's inverse rotation
    assert chars["A"]["matrix"][:4] == pytest.approx((0.0, 1.0, -1.0, 0.0), abs=1e-9)
    assert chars["B"]["matrix"][:4] == pytest.approx((0.0, -1.0, 1.0, 0.0), abs=1e-9)


def test_a_circle_and_an_arc_land_where_they_were_asked(tmp_path):
    """fpdf2 2.8.8 takes a centre for `circle` and a bounding-box corner for
    `arc`, and its own docstring for `circle` still says otherwise. This is
    the test that would have caught believing the prose."""
    _sheet(
        tmp_path,
        page=[300, 200],
        blocks=[
            {
                "kind": "vector",
                "origin": "bottom_left",
                "at": [20, 20],
                "items": [
                    {"kind": "circle", "center": [50, 50], "radius": 20},
                    {
                        "kind": "arc",
                        "center": [150, 50],
                        "radius": 20,
                        "start_deg": 0,
                        "end_deg": 90,
                    },
                ],
            }
        ],
    )
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        circle, arc = doc.pages[0].curves
    assert mm(circle["x0"]) == pytest.approx(50.0, abs=0.05)
    assert mm(circle["x1"]) == pytest.approx(90.0, abs=0.05)
    assert mm(circle["top"]) == pytest.approx(200.0 - 90.0, abs=0.05)
    assert mm(circle["bottom"]) == pytest.approx(200.0 - 50.0, abs=0.05)
    # the first quadrant only: right of and above the centre (170, 70)
    assert mm(arc["x0"]) == pytest.approx(170.0, abs=0.05)
    assert mm(arc["x1"]) == pytest.approx(190.0, abs=0.05)
    assert mm(arc["bottom"]) == pytest.approx(200.0 - 70.0, abs=0.05)
    assert "c\n" in _stream(tmp_path / "v.pdf"), "an arc must reach the stream as curves"


def test_a_filled_path_fills_in_the_colour_it_was_given(tmp_path):
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "items": [
                    {
                        "kind": "path",
                        "points": [[50, 50], [70, 50], [60, 70]],
                        "fill": "#ff0000",
                    }
                ],
            }
        ],
    )
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        (shape,) = doc.pages[0].curves
    assert shape["fill"] is True
    assert tuple(round(c, 3) for c in shape["non_stroking_color"]) == (1.0, 0.0, 0.0)


def test_a_polyline_and_a_rectangle_reach_the_stream_as_such(tmp_path):
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "items": [
                    {"kind": "polyline", "points": [[10, 10], [30, 40], [50, 10]]},
                    {"kind": "rect", "at": [60, 60], "size": [40, 20]},
                ],
            }
        ],
    )
    stream = _stream(tmp_path / "v.pdf")
    assert " re S" in stream, "a rectangle should be one `re`, not four lines"
    assert stream.count(" l\n") >= 2, "a polyline is line-to operators"
    with pdfplumber.open(str(tmp_path / "v.pdf")) as doc:
        page = doc.pages[0]
        (box,) = page.rects
    assert mm(box["x0"]) == pytest.approx(60.0, abs=FPDF_ROUNDING_MM)
    assert mm(box["top"]) == pytest.approx(60.0, abs=FPDF_ROUNDING_MM)


def test_a_closed_polyline_returns_to_its_start(tmp_path):
    _sheet(
        tmp_path,
        page=[200, 200],
        blocks=[
            {
                "kind": "vector",
                "items": [
                    {
                        "kind": "polyline",
                        "points": [[10, 10], [50, 10], [50, 40]],
                        "close": True,
                    }
                ],
            }
        ],
    )
    assert " h\n" in _stream(tmp_path / "v.pdf")


# -- the whole thing, as a drawing sheet ------------------------------------


def test_a_partkiln_style_sheet_composes_end_to_end(tmp_path):
    """The gap in one test: an A3 landscape sheet with a border, a title
    block, a part outline at 1:2, a hidden edge and a dimension - drawn
    through TEE's own lane, with no partkiln[pdf] extra anywhere."""
    result = _sheet(
        tmp_path,
        "sheet.pdf",
        page="A3",
        orientation="landscape",
        title="BRACKET W1",
        blocks=[
            {
                "kind": "vector",
                "origin": "bottom_left",
                "units": "mm",
                "items": [
                    {"kind": "rect", "at": [10, 10], "size": [400, 277], "width_mm": 0.7},
                    {"kind": "rect", "at": [230, 10], "size": [180, 40], "width_mm": 0.5},
                    {"kind": "text", "at": [235, 35], "text": "BRACKET W1", "size_pt": 11},
                    {"kind": "text", "at": [235, 20], "text": "SCALE 1:2  MM", "size_pt": 8},
                ],
            },
            {
                "kind": "vector",
                "origin": "bottom_left",
                "units": "mm",
                "scale": "1:2",
                "at": [40, 120],
                "items": [
                    {"kind": "rect", "at": [0, 0], "size": [120, 80]},
                    {"kind": "circle", "center": [20, 20], "radius": 3.3},
                    {"kind": "circle", "center": [100, 60], "radius": 3.3},
                    {"kind": "line", "from": [0, 40], "to": [120, 40], "dash": "hidden"},
                    {"kind": "line", "from": [0, -20], "to": [120, -20], "arrows": "both"},
                    {
                        "kind": "text",
                        "at": [60, -18],
                        "text": "120",
                        "align": "center",
                        "size_pt": 9,
                    },
                ],
            },
        ],
    )
    assert result["pages"] == 1
    assert result["page_mm"] == [420.0, 297.0]
    assert result["vector_items"] == 4 + 6
    assert [f["scale"] for f in result["vector_frames"]] == ["1:1", "1:2"]

    box = pypdf.PdfReader(str(tmp_path / "sheet.pdf")).pages[0].mediabox
    assert float(box.width) == pytest.approx(420.0 * PT_PER_MM, abs=0.01)

    with pdfplumber.open(str(tmp_path / "sheet.pdf")) as doc:
        page = doc.pages[0]
        rects = sorted(page.rects, key=lambda r: -r["width"])
        words = {w["text"] for w in page.extract_words()}
        dashed = [ln for ln in page.lines if ln["dash"][0]]
        filled = [c for c in page.curves if c.get("fill")]
        holes = [c for c in page.curves if not c.get("fill")]
    # border, title block, and the part outline at half size
    assert mm(rects[0]["width"]) == pytest.approx(400.0, abs=FPDF_ROUNDING_MM)
    assert mm(rects[1]["width"]) == pytest.approx(180.0, abs=FPDF_ROUNDING_MM)
    assert mm(rects[2]["width"]) == pytest.approx(60.0, abs=FPDF_ROUNDING_MM)
    assert mm(rects[2]["height"]) == pytest.approx(40.0, abs=FPDF_ROUNDING_MM)
    assert {"BRACKET", "W1", "SCALE", "1:2", "MM", "120"} <= words
    # the hidden edge is dashed, and its dash is paper mm, not model mm
    assert len(dashed) == 1
    assert [round(mm(v), 2) for v in dashed[0]["dash"][0]] == [2.5, 1.5]
    # two arrowheads, and two Ø6.6 holes drawn at Ø3.3 on the paper
    assert len(filled) == 2
    assert len(holes) == 2
    assert mm(holes[0]["x1"] - holes[0]["x0"]) == pytest.approx(3.3, abs=0.05)


# -- refusals: each one names the exact fix ---------------------------------


def test_an_unstated_unit_is_not_guessed(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(
            tmp_path,
            blocks=[{"kind": "vector", "units": "furlong", "items": [{"kind": "line"}]}],
        )
    assert err.value.code == "pdf_bad_units"
    assert "mm" in err.value.fix and "lies" in err.value.fix


def test_a_bad_origin_names_both_conventions(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(tmp_path, blocks=[{"kind": "vector", "origin": "middle", "items": [{}]}])
    assert err.value.code == "pdf_bad_origin"
    assert "top_left" in err.value.fix and "bottom_left" in err.value.fix


@pytest.mark.parametrize("bad", ["one:two", "1:0", -2, "half"])
def test_a_scale_that_is_not_a_scale_is_refused(tmp_path, bad):
    with pytest.raises(TeeError) as err:
        _sheet(
            tmp_path,
            blocks=[
                {
                    "kind": "vector",
                    "scale": bad,
                    "items": [{"kind": "line", "from": [0, 0], "to": [1, 1]}],
                }
            ],
        )
    assert err.value.code == "pdf_bad_scale"


def test_a_centre_line_is_refused_by_name_rather_than_faked(tmp_path):
    """The backend carries one dash and one gap. A centre line's
    long-short-long array cannot be expressed, so it is not approximated
    behind the caller's back."""
    with pytest.raises(TeeError) as err:
        _sheet(
            tmp_path,
            blocks=[
                {
                    "kind": "vector",
                    "items": [{"kind": "line", "from": [0, 0], "to": [10, 0], "dash": "center"}],
                }
            ],
        )
    assert err.value.code == "pdf_bad_dash"
    assert "centre line" in err.value.fix and "explicit `line` items" in err.value.fix


def test_an_unknown_item_kind_lists_the_kinds(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(tmp_path, blocks=[{"kind": "vector", "items": [{"kind": "spline"}]}])
    assert err.value.code == "pdf_bad_vector"
    for kind in ("line", "polyline", "rect", "circle", "arc", "path", "text"):
        assert kind in err.value.fix


def test_an_empty_vector_block_says_what_an_item_looks_like(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(tmp_path, blocks=[{"kind": "vector", "items": []}])
    assert err.value.code == "pdf_bad_vector"
    assert '"kind": "line"' in err.value.fix


def test_a_point_that_is_not_a_point_says_which_key(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(
            tmp_path,
            blocks=[{"kind": "vector", "items": [{"kind": "line", "from": [0], "to": [1, 1]}]}],
        )
    assert err.value.code == "pdf_bad_point"
    assert "'from'" in err.value.message


def test_a_missing_radius_names_the_key(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(
            tmp_path,
            blocks=[{"kind": "vector", "items": [{"kind": "circle", "center": [0, 0]}]}],
        )
    assert err.value.code == "pdf_bad_vector"
    assert "radius" in err.value.fix


def test_an_unknown_page_size_lists_the_known_ones(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(tmp_path, page="A9", blocks=[{"kind": "spacer"}])
    assert err.value.code == "pdf_bad_page"
    assert "a3" in err.value.fix and "letter" in err.value.fix


def test_an_unknown_orientation_says_landscape_swaps(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(tmp_path, orientation="sideways", blocks=[{"kind": "spacer"}])
    assert err.value.code == "pdf_bad_page"
    assert "landscape" in err.value.fix.lower()


def test_a_zero_area_page_is_refused(tmp_path):
    with pytest.raises(TeeError) as err:
        _sheet(tmp_path, page=[0, 100], blocks=[{"kind": "spacer"}])
    assert err.value.code == "pdf_bad_page"


# -- the surface and the trust table ----------------------------------------


def test_the_vector_block_added_no_tool_and_no_capability(tmp_path):
    """A drawing block is more `pdf_compose`, not another tool. And it still
    only writes a file where it was told to, so the capability is unchanged."""
    from tee.app import TeeApp
    from tee.kernel import trust
    from tee.pdf import register_pdf_tools

    app = TeeApp({}, project_root=tmp_path)
    before = set(app.registry.names())
    register_pdf_tools(app, tmp_path)
    assert set(app.registry.names()) - before == {"pdf_compose", "pdf_edit"}
    assert trust.capability_for("pdf_compose") == "write-artifacts"
    assert "vector" in pdf.BLOCK_KINDS


def test_the_frame_maths_is_the_same_in_both_directions(tmp_path):
    """A round trip through the frame, so the transform is pinned as
    arithmetic and not only as ink on a page."""
    frame = pdf.VectorFrame(
        units="mm",
        origin="bottom_left",
        unit_mm=1.0,
        scale=0.5,
        scale_text="1:2",
        at_mm=(20.0, 30.0),
        page_h_mm=297.0,
    )
    assert frame.point((100.0, 0.0)) == (70.0, 267.0)
    assert frame.length(100.0) == 50.0
    assert math.isclose(frame.point((0.0, 100.0))[1], 297.0 - 80.0)
    assert frame.summary()["scale"] == "1:2"


# -- the numbers a PDF cannot carry ------------------------------------------------


@pytest.mark.parametrize(
    ("bad", "code"),
    [
        ({"kind": "line", "from": [float("nan"), 0], "to": [10, 0]}, "pdf_bad_point"),
        ({"kind": "line", "from": [0, 0], "to": [float("inf"), 0]}, "pdf_bad_point"),
        ({"kind": "polyline", "points": [[0, 0], [float("nan"), 1]]}, "pdf_bad_point"),
        ({"kind": "circle", "center": [0, 0], "radius": float("nan")}, "pdf_bad_vector"),
        (
            {"kind": "arc", "center": [0, 0], "radius": 5, "start_deg": float("nan")},
            "pdf_bad_vector",
        ),
        (
            {"kind": "line", "from": [0, 0], "to": [1, 1], "width_mm": float("nan")},
            "pdf_bad_vector",
        ),
        ({"kind": "line", "from": [0, 0], "to": [1, 1], "dash": [float("nan"), 1]}, "pdf_bad_dash"),
        ({"kind": "text", "at": [0, 0], "text": "x", "size_pt": float("nan")}, "pdf_bad_vector"),
        ({"kind": "text", "at": [0, 0], "text": "x", "angle_deg": float("inf")}, "pdf_bad_vector"),
    ],
)
def test_a_non_finite_number_is_refused_not_written(tmp_path, bad, code):
    """MEASURED 2026-09-04, fpdf2 2.8.8: a float goes into the content stream
    verbatim, so `[nan, 0]` wrote `nan 28.35 m ... S` - a page no reader can
    parse - while compose answered `ok: true`. Fail loud and cheap instead."""
    with pytest.raises(TeeError) as caught:
        pdf.compose(
            {
                "out": str(tmp_path / "v.pdf"),
                "blocks": [{"kind": "vector", "units": "mm", "at": [10, 10], "items": [bad]}],
            }
        )
    assert caught.value.code == code
    assert caught.value.fix
    assert not (tmp_path / "v.pdf").exists()


@pytest.mark.parametrize("scale", [float("inf"), float("nan")])
def test_a_non_finite_scale_is_refused(tmp_path, scale):
    """The frame multiplies every coordinate, so one bad scale poisons the sheet."""
    with pytest.raises(TeeError) as caught:
        pdf.compose(
            {
                "out": str(tmp_path / "v.pdf"),
                "blocks": [
                    {
                        "kind": "vector",
                        "units": "mm",
                        "scale": scale,
                        "at": [10, 10],
                        "items": [{"kind": "line", "from": [0, 0], "to": [10, 0]}],
                    }
                ],
            }
        )
    assert caught.value.code == "pdf_bad_scale"
