"""The pattern kernel (A53 P1): geometry, model, allowance, DXF, plotting.

No Blender, no GPU, no network. The DXF and plotter cases assert against
files that were actually written and read back, because both of these are
formats where "it looked right" and "it is right" diverge silently - a
pattern that prints at 97% or loses its corner tags fails on the cutting
table, not in a viewer.
"""

from __future__ import annotations

import math
import re
from itertools import pairwise

import pytest

from seamkiln.pattern import plot
from seamkiln.pattern.allowance import (
    AllowanceError,
    add_seam_allowance,
    fabric_consumption,
    offset_outline,
    sew_line,
)
from seamkiln.pattern.dxf import AAMA, ASTM, DxfDialectError, dialect, read_dxf, write_dxf
from seamkiln.pattern.fixtures import tee_block
from seamkiln.pattern.geometry import (
    Vertex,
    VertexKind,
    arc,
    area,
    join,
    line,
    perimeter,
    point_at,
    slice_run,
)
from seamkiln.pattern.model import (
    EdgeRef,
    GradeRule,
    InternalLine,
    LineKind,
    Mark,
    MarkKind,
    Panel,
    Pattern,
    Seam,
    grade,
    mirror,
    true_up,
    unfold,
)

PT_PER_MM = 72.0 / 25.4


def square(side: float = 100.0) -> Panel:
    return Panel(
        id="SQ",
        outline=[Vertex(0, 0), Vertex(side, 0), Vertex(side, side), Vertex(0, side)],
    )


# -- geometry ----------------------------------------------------------------


def test_area_and_perimeter_are_millimetres() -> None:
    panel = square(100.0)
    assert panel.area_mm2 == pytest.approx(10_000.0)
    assert panel.perimeter_mm == pytest.approx(400.0)


def test_winding_is_normalised_so_a_positive_offset_grows() -> None:
    clockwise = Panel(id="CW", outline=[Vertex(0, 0), Vertex(0, 10), Vertex(10, 10), Vertex(10, 0)])
    assert clockwise.area_mm2 == pytest.approx(100.0)
    grown = offset_outline(clockwise.outline, 1.0)
    assert area(grown) > clockwise.area_mm2


def test_arc_sampling_respects_its_sag_tolerance() -> None:
    radius, tolerance = 200.0, 0.05
    points = arc((0.0, 0.0), radius, 0.0, 90.0, tolerance=tolerance)
    for a, b in pairwise(points):
        chord = math.hypot(b.x - a.x, b.y - a.y)
        sag = radius - math.sqrt(max(radius**2 - (chord / 2) ** 2, 0.0))
        assert sag <= tolerance * 1.05, "a chord sags further than the caller allowed"


def test_join_keeps_a_corner_that_meets_a_curve() -> None:
    joined = join(line((0, 0), (10, 0)), arc((10, 10), 10.0, -90.0, 0.0))
    assert joined[0].kind is VertexKind.TURN
    shared = next(v for v in joined if abs(v.x - 10) < 1e-9 and abs(v.y) < 1e-9)
    assert shared.kind is VertexKind.TURN, "the joint downgraded a corner to a curve point"


def test_slice_run_measures_the_fraction_it_promises() -> None:
    run = line((0, 0), (100, 0))
    assert perimeter(slice_run(run, 0.0, 0.5), closed=False) == pytest.approx(50.0)
    assert point_at(run, 0.25) == pytest.approx((25.0, 0.0))


# -- model -------------------------------------------------------------------


def test_edges_come_from_corners_and_close_around_the_ring() -> None:
    panel = square()
    assert len(panel.edges()) == 4
    assert panel.edge_ids() == ["SQ#0", "SQ#1", "SQ#2", "SQ#3"]
    for k in range(4):
        assert panel.edge_length(EdgeRef("SQ", k)) == pytest.approx(100.0)


def test_an_explicitly_closed_ring_does_not_grow_a_zero_length_edge() -> None:
    """The defect this normalisation exists for: a repeated first vertex makes
    a final edge of length 0.0, and a 0 mm seam matches anything."""
    explicit = Panel(
        id="X",
        outline=[Vertex(0, 0), Vertex(10, 0), Vertex(10, 10), Vertex(0, 10), Vertex(0, 0)],
    )
    assert len(explicit.outline) == 4
    assert min(explicit.edge_length(EdgeRef("X", k)) for k in range(4)) > 0.0


def test_a_circle_with_no_corners_is_one_edge_not_an_error() -> None:
    ring = [
        Vertex(math.cos(t) * 50, math.sin(t) * 50, VertexKind.CURVE)
        for t in [i * math.tau / 32 for i in range(32)]
    ]
    assert len(Panel(id="O", outline=ring).edges()) == 1


def test_true_up_reports_millimetres_not_a_verdict() -> None:
    a = Panel(id="A", outline=[Vertex(0, 0), Vertex(100, 0), Vertex(100, 50), Vertex(0, 50)])
    b = Panel(id="B", outline=[Vertex(0, 0), Vertex(107, 0), Vertex(107, 50), Vertex(0, 50)])
    pattern = Pattern(panels=[a, b], seams=[Seam(EdgeRef("A", 0), EdgeRef("B", 0), id="s")])
    (check,) = true_up(pattern)
    assert check.mismatch_mm == pytest.approx(7.0)
    assert not check.ok


def test_sleeve_head_ease_is_declared_not_reported_as_an_error() -> None:
    """The cap is 4.5 mm longer than the armhole ON PURPOSE. Declared as
    gather, it reads as 0; undeclared it would be a standing false alarm in
    every report, which is how real warnings get ignored."""
    from seamkiln.pattern.fixtures import SLEEVE_HEAD_EASE

    assert 1.01 < SLEEVE_HEAD_EASE < 1.10
    checks = {c.seam_id: c for c in true_up(tee_block(), tolerance_mm=0.5)}
    assert abs(checks["armhole-right-front"].mismatch_mm) < 0.1
    assert checks["armhole-right-front"].a_mm > checks["armhole-right-front"].b_mm


def test_gather_is_an_intention_the_check_measures_against() -> None:
    frill = Panel(id="F", outline=[Vertex(0, 0), Vertex(200, 0), Vertex(200, 50), Vertex(0, 50)])
    band = Panel(id="B", outline=[Vertex(0, 0), Vertex(100, 0), Vertex(100, 50), Vertex(0, 50)])
    pattern = Pattern(
        panels=[frill, band],
        seams=[Seam(EdgeRef("F", 0), EdgeRef("B", 0), gather=2.0, id="ruffle")],
    )
    (check,) = true_up(pattern)
    assert check.mismatch_mm == pytest.approx(0.0), "a 2:1 gather is not a 100 mm error"


def test_a_seam_can_claim_part_of_an_edge() -> None:
    long_panel = Panel(
        id="L", outline=[Vertex(0, 0), Vertex(200, 0), Vertex(200, 50), Vertex(0, 50)]
    )
    short = Panel(id="S", outline=[Vertex(0, 0), Vertex(100, 0), Vertex(100, 50), Vertex(0, 50)])
    pattern = Pattern(
        panels=[long_panel, short],
        seams=[Seam(EdgeRef("L", 0, 0.0, 0.5), EdgeRef("S", 0), id="half")],
    )
    (check,) = true_up(pattern)
    assert check.a_mm == pytest.approx(100.0)
    assert check.mismatch_mm == pytest.approx(0.0)


def test_mirror_and_unfold() -> None:
    half = Panel(id="H", outline=[Vertex(0, 0), Vertex(60, 0), Vertex(60, 100), Vertex(0, 100)])
    assert mirror(half, axis="y").area_mm2 == pytest.approx(half.area_mm2)
    whole = unfold(half, axis="y", at=0.0)
    assert whole.area_mm2 == pytest.approx(half.area_mm2 * 2)


def test_grade_moves_only_the_points_the_rule_names() -> None:
    pattern = Pattern(panels=[square(100.0)])
    rule = GradeRule("size", dx={1: 10.0, 2: 10.0})
    graded = grade(pattern, rule, steps=2)
    assert graded.panels[0].area_mm2 == pytest.approx(12_000.0)
    assert pattern.panels[0].area_mm2 == pytest.approx(10_000.0), "grade mutated its input"


def test_summary_is_compact_and_holds_no_vertices() -> None:
    text = repr(tee_block().summary())
    assert "Vertex" not in text
    assert len(text) < 1200


def test_missing_panel_names_what_exists() -> None:
    with pytest.raises(KeyError, match="FRONT"):
        tee_block().panel("SLEEVE_X")


# -- seam allowance ----------------------------------------------------------


def test_seam_allowance_grows_the_piece_and_keeps_the_sew_line() -> None:
    panel = square(100.0)
    cut = add_seam_allowance(panel, 10.0)
    assert cut.area_mm2 == pytest.approx(120.0 * 120.0)  # mitred corners, not rounded
    assert cut.seam_allowance_mm == 10.0
    assert any(i.kind is LineKind.SEW for i in cut.internals)
    assert area(sew_line(cut)) == pytest.approx(panel.area_mm2)


def test_an_allowance_that_would_consume_the_panel_refuses_with_the_reason() -> None:
    with pytest.raises(AllowanceError, match="narrowest"):
        offset_outline(square(20.0).outline, -15.0, context="tiny")


def test_a_negative_allowance_is_refused_by_name() -> None:
    with pytest.raises(AllowanceError, match="must be positive"):
        add_seam_allowance(square(), -5.0)


def test_fabric_consumption_reports_how_badly_a_piece_nests() -> None:
    triangle = Panel(id="T", outline=[Vertex(0, 0), Vertex(100, 0), Vertex(0, 100)])
    report = fabric_consumption(triangle)
    assert report["fill_ratio"] == pytest.approx(0.5, abs=0.01)


# -- DXF interchange ---------------------------------------------------------


def test_dxf_round_trip_is_lossless(tmp_path) -> None:
    """The acceptance case: pieces, layers, notches and area all survive."""
    original = tee_block()
    path = tmp_path / "tee.dxf"
    written = write_dxf(original, path, flavour="astm")
    assert written["pieces"] == 4
    assert written["entities"]["boundary"] == 4
    assert written["entities"]["notch"] == 8
    assert written["entities"]["drill"] == 1

    back, report = read_dxf(path, flavour="astm")
    assert report.pieces == 4
    assert report.unknown_layers == {}
    assert report.skipped_blocks == ["*Model_Space", "*Paper_Space"]
    assert report.insunits == 4  # millimetres survived the trip

    for piece in original.panels:
        got = back.panel(piece.id)
        assert got.area_mm2 == pytest.approx(piece.area_mm2, rel=1e-6)
        assert len(got.edges()) == len(piece.edges()), "turn/curve tags were lost"
        assert len(got.marks) == len(piece.marks)
        assert len(got.internals) == len(piece.internals)


def test_units_are_converted_on_the_way_in(tmp_path) -> None:
    import ezdxf

    doc = ezdxf.new(dxfversion="R2000", setup=False)
    doc.header["$INSUNITS"] = 1  # inches
    block = doc.blocks.new("PIECE")
    block.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=True, dxfattribs={"layer": "1"})
    doc.modelspace().add_blockref("PIECE", (0, 0))
    path = tmp_path / "inches.dxf"
    doc.saveas(path)

    pattern, report = read_dxf(path)
    assert report.scale_mm == pytest.approx(25.4)
    assert pattern.panels[0].area_mm2 == pytest.approx(25.4**2)


def test_an_unknown_layer_refuses_and_names_the_dialect(tmp_path) -> None:
    import ezdxf

    doc = ezdxf.new(dxfversion="R2000", setup=False)
    block = doc.blocks.new("PIECE")
    block.add_lwpolyline([(0, 0), (10, 0), (10, 10)], close=True, dxfattribs={"layer": "1"})
    block.add_lwpolyline([(1, 1), (2, 2)], dxfattribs={"layer": "77"})  # not in any dialect
    doc.modelspace().add_blockref("PIECE", (0, 0))
    path = tmp_path / "odd.dxf"
    doc.saveas(path)

    with pytest.raises(DxfDialectError) as excinfo:
        read_dxf(path, flavour="astm")
    message = str(excinfo.value)
    assert "layer 77" in message
    assert "'astm'" in message
    assert "strict=False" in message  # the fix is named, not just the problem

    lenient, report = read_dxf(path, flavour="astm", strict=False)
    assert report.unknown_layers == {"77": 1}
    assert len(lenient.panels) == 1


def test_aama_refuses_a_feature_it_does_not_define(tmp_path) -> None:
    """AAMA has no internal-cutout layer. Refusing beats writing it to layer 8
    and letting a cutter treat a hole as decoration."""
    panel = Panel(
        id="P",
        outline=[Vertex(0, 0), Vertex(100, 0), Vertex(100, 100), Vertex(0, 100)],
        internals=[
            InternalLine(
                LineKind.CUTOUT,
                [Vertex(20, 20), Vertex(40, 20), Vertex(40, 40), Vertex(20, 40)],
                closed=True,
            )
        ],
    )
    with pytest.raises(DxfDialectError, match="no layer for 'cutout'"):
        write_dxf(Pattern(panels=[panel]), tmp_path / "x.dxf", flavour="aama")

    assert write_dxf(Pattern(panels=[panel]), tmp_path / "y.dxf", flavour="astm")["pieces"] == 1


def test_dialects_declare_whether_they_were_verified() -> None:
    assert ASTM.verified is True and "D6673" in ASTM.source
    assert AAMA.verified is False, "the AAMA layer map is second-hand; do not claim otherwise"
    assert AAMA.notes
    with pytest.raises(DxfDialectError, match="seamkiln writes"):
        dialect("gerber")


def test_written_dxf_reports_the_r13_gap_rather_than_implying_it(tmp_path) -> None:
    report = write_dxf(tee_block(), tmp_path / "t.dxf", flavour="astm")
    assert report["dxfversion"] == "R2000"
    assert "R13" in report["dxfversion_note"]
    assert report["layout_blocks_present"] == ["*Model_Space", "*Paper_Space"]


# -- plotting ----------------------------------------------------------------


def test_svg_declares_millimetres_at_one_to_one(tmp_path) -> None:
    path = tmp_path / "t.svg"
    info = plot.to_svg(tee_block(), path)
    text = path.read_text()
    assert f'width="{info["width_mm"]}mm"' in text
    assert f'viewBox="0 0 {info["width_mm"]} {info["height_mm"]}"' in text


def test_pdf_prints_at_true_one_to_one(tmp_path) -> None:
    """A 100 x 50 mm rectangle must be 100 x 50 mm in the finished PDF.

    Measured out of the page's own content stream, not from the metadata:
    the page box being A4 says nothing about whether the drawing was scaled.
    """
    pypdf = pytest.importorskip("pypdf")
    rectangle = Panel(
        id="R", outline=[Vertex(0, 0), Vertex(100, 0), Vertex(100, 50), Vertex(0, 50)]
    )
    path = tmp_path / "ruler.pdf"
    info = plot.to_pdf(Pattern(name="ruler", panels=[rectangle]), path, page="A4")
    assert info["pages"] == 1

    page = pypdf.PdfReader(str(path)).pages[0]
    assert float(page.mediabox.width) / PT_PER_MM == pytest.approx(210.0, abs=0.01)

    stream = page.get_contents().get_data().decode("latin-1")
    segments = [
        (float(a), float(b), float(c), float(d))
        for a, b, c, d in re.findall(r"([\d.]+) ([\d.]+) m\s+([\d.]+) ([\d.]+) l", stream)
    ]
    assert segments, "the page drew no line segments at all"
    horizontals = {
        round(abs(x2 - x1) / PT_PER_MM, 2) for x1, y1, x2, y2 in segments if abs(y2 - y1) < 0.01
    }
    verticals = {
        round(abs(y2 - y1) / PT_PER_MM, 2) for x1, y1, x2, y2 in segments if abs(x2 - x1) < 0.01
    }
    assert 100.0 in horizontals, f"no 100 mm horizontal; got {sorted(horizontals)}"
    assert 50.0 in verticals, f"no 50 mm vertical; got {sorted(verticals)}"


def test_a_big_pattern_tiles_and_says_how_many_pages(tmp_path) -> None:
    info = plot.to_pdf(tee_block(), tmp_path / "tee.pdf", page="A4")
    assert info["pages"] == info["tiles"]["rows"] * info["tiles"]["cols"] > 1
    assert info["scale"] == "1:1"
    single = plot.to_pdf(tee_block(), tmp_path / "roll.pdf", page="PLOTTER_1370")
    assert single["pages"] == 1, "a 1.37 m roll should not need tiling for a tee"


def test_unknown_page_size_lists_what_exists(tmp_path) -> None:
    with pytest.raises(ValueError, match="A4"):
        plot.to_pdf(tee_block(), tmp_path / "x.pdf", page="A7")


def test_piece_report_is_the_tech_pack_row(tmp_path) -> None:
    row = plot.piece_report(tee_block().panel("BACK"))
    assert row["notches"] == 3 and row["drills"] == 1 and row["grain"] is True
    assert row["area_mm2"] > 0 and row["perimeter_mm"] > 0


# -- the fixture itself ------------------------------------------------------


def test_the_tee_block_is_sewable() -> None:
    """Every seam closes: the fixture is a garment, not four shapes near each
    other. Tolerance is half a millimetre - tighter than the 1 mm a pattern
    maker would accept - because a drafting error should surface here rather
    than in the drape."""
    pattern = tee_block()
    assert len(pattern.panels) == 4
    assert {p.id for p in pattern.panels} == {"FRONT", "BACK", "SLEEVE_L", "SLEEVE_R"}
    assert len(pattern.seams) == 10  # 2 side, 2 shoulder, 4 armhole, 2 underarm
    for check in true_up(pattern, tolerance_mm=0.5):
        assert abs(check.mismatch_mm) <= 0.5, f"{check.seam_id} is out by {check.mismatch_mm} mm"
    front = pattern.panel("FRONT")
    assert 0.25e6 < front.area_mm2 < 0.40e6  # a tee front, in mm^2
    assert any(m.kind is MarkKind.NOTCH_V for m in front.marks)
    assert any(i.kind is LineKind.GRAIN for i in front.internals)


def test_marks_and_lines_survive_a_mirror() -> None:
    original = tee_block().panel("BACK")
    flipped = mirror(original)
    assert len(flipped.marks) == len(original.marks)
    assert [m.kind for m in flipped.marks] == [m.kind for m in original.marks]
    assert isinstance(flipped.marks[0], Mark)


# -- fabric ------------------------------------------------------------------


def test_every_bundled_fabric_declares_its_tier_honestly() -> None:
    from seamkiln.pattern.fabric import Tier, catalogue, fabric

    for row in catalogue():
        assert row["tier"] == Tier.PLAUSIBLE, (
            "a bundled row claims to be measured; only a real test report may. "
            "ArcSim's measured set is non-profit-only and cannot ship."
        )
    assert fabric("denim_12oz").gsm > fabric("chiffon").gsm * 5


def test_stiffer_cloth_gets_lower_compliance() -> None:
    from seamkiln.pattern.fabric import fabric

    denim = fabric("denim_12oz").compliances()
    chiffon = fabric("chiffon").compliances()
    assert denim["bending"] < chiffon["bending"], "denim should resist bending more than chiffon"
    assert denim["shear"] < chiffon["shear"]


def test_unknown_fabric_lists_what_exists() -> None:
    from seamkiln.pattern.fabric import fabric

    with pytest.raises(KeyError, match="cotton_jersey"):
        fabric("neoprene")


def test_yardage_says_out_loud_that_it_is_an_estimate() -> None:
    from seamkiln.pattern.fabric import FabricSheet, fabric

    sheet = FabricSheet(fabric("cotton_jersey"))
    result = sheet.yardage(tee_block().total_area_mm2)
    assert result["estimate"] is True
    assert 0.5 < result["length_m"] < 3.0  # a tee's worth of jersey
    assert result["mass_g"] > 100
