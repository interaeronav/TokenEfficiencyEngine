"""Reading the DXF that pattern CAD actually writes.

Two CLO 2024 exports (DXF-AAMA/ASTM, R12) read as zero pieces on
2026-09-04 for three reasons, each held here on a synthetic file built the
way CLO builds them: the boundary is an R12 heavy POLYLINE, not an
LWPOLYLINE; R12 has no `$INSUNITS`, the unit is the header's "UNITS:
METRIC", and METRIC means centimetres; and the piece name is the "PIECE
NAME:" system text, not the last TEXT in the block. Layers 84/85 turned out
to be the standard's quality-validation curves - dense copies of the curved
runs, not a sew line (they coincide with the boundary to 0.1 mm and enclose
LESS area) - so they are counted and measured, never imported.
"""

from __future__ import annotations

import math

import ezdxf
import pytest

from seamkiln.pattern.allowance import add_seam_allowance, sew_line
from seamkiln.pattern.dxf import read_dxf, write_dxf
from seamkiln.pattern.fixtures import tee_block
from seamkiln.pattern.geometry import VertexKind
from seamkiln.pattern.model import LineKind, MarkKind, Pattern

# a 40 x 60 cm front whose top edge is an arc through five curve points
CORNERS = [(0.0, 0.0), (40.0, 0.0), (40.0, 60.0), (0.0, 60.0)]
ARC = [(40.0 - 40.0 * (i / 6.0), 60.0 + 6.0 * math.sin(math.pi * i / 6.0)) for i in range(1, 6)]
BOUNDARY = CORNERS[:3] + ARC + CORNERS[3:]


def _clo_style(path, *, units: str | None = "METRIC", extra_boundary: bool = False) -> None:
    doc = ezdxf.new("R12")
    space = doc.modelspace()
    y = 100.0
    for line in (
        "STYLE NAME: Camiseta",
        "AUTHOR: CLO Virtual Fashion Inc.",
        "PRODUCT: CLO Network OnlineAuth 2024.1.260",
        "SAMPLE SIZE: M",
    ) + ((f"UNITS: {units}",) if units else ()):
        space.add_text(line, dxfattribs={"layer": "1", "height": 1.0, "insert": (0.0, y)})
        y -= 2.0
    block = doc.blocks.new("Frente_M")
    block.add_polyline2d(BOUNDARY, close=True, dxfattribs={"layer": "1"})
    if extra_boundary:
        block.add_polyline2d([(1, 1), (3, 1), (3, 3)], close=True, dxfattribs={"layer": "1"})
    for x, y in CORNERS:
        block.add_point((x, y), dxfattribs={"layer": "2"})
    for x, y in ARC:
        block.add_point((x, y), dxfattribs={"layer": "3"})
    block.add_point((40.0, 30.0), dxfattribs={"layer": "4"})
    block.add_line((20.0, 5.0), (20.0, 55.0), dxfattribs={"layer": "7"})
    block.add_polyline2d([(5.0, 10.0), (35.0, 10.0)], dxfattribs={"layer": "8"})
    # the quality-validation copy of the arc, 60 samples, and of the internal
    dense = [
        (40.0 - 40.0 * (i / 60.0), 60.0 + 6.0 * math.sin(math.pi * i / 60.0)) for i in range(61)
    ]
    block.add_polyline2d(dense, close=True, dxfattribs={"layer": "84"})
    block.add_polyline2d([(5.0, 10.0), (20.0, 10.0), (35.0, 10.0)], dxfattribs={"layer": "85"})
    for i, line in enumerate(("PIECE NAME: Frente", "SIZE: M", "QUANTITY: 1", "# 180")):
        block.add_text(line, dxfattribs={"layer": "1", "height": 0.5, "insert": (2.0, 2.0 + i)})
    space.add_blockref("Frente_M", (0.0, 0.0))
    doc.saveas(path)


def test_a_clo_export_reads_in_millimetres_with_its_names_and_tags(tmp_path) -> None:
    path = tmp_path / "clo.dxf"
    _clo_style(path)
    pattern, report = read_dxf(path)

    assert report.pieces == 1
    assert report.insunits == 0, "R12 carries no $INSUNITS"
    assert report.units_source == "header UNITS: METRIC"
    assert report.scale_mm == 10.0
    assert report.unknown_layers == {} and report.notes == []
    assert report.header["AUTHOR"] == "CLO Virtual Fashion Inc."
    assert pattern.name == "Camiseta"

    (piece,) = pattern.panels
    assert (piece.id, piece.name) == ("Frente_M", "Frente")
    x0, y0, x1, y1 = piece.bbox
    assert (x1 - x0, y1 - y0) == pytest.approx((400.0, 660.0))
    assert sum(v.kind is VertexKind.TURN for v in piece.outline) == 4
    assert sum(v.kind is VertexKind.CURVE for v in piece.outline) == 5
    assert len(piece.edges()) == 4, "the arc reads as one curved run"
    assert [m.kind for m in piece.marks] == [MarkKind.NOTCH_SLIT]
    assert piece.marks[0].x == pytest.approx(400.0)
    assert sorted(i.kind for i in piece.internals) == [LineKind.GRAIN, LineKind.INTERNAL]
    assert piece.meta["size"] == "M" and piece.meta["quantity"] == "1"
    assert piece.meta["piece_number"] == "180"
    assert "outline_is" not in piece.meta and piece.seam_allowance_mm == 0.0


def test_validation_curves_are_measured_and_never_imported(tmp_path) -> None:
    """Layer 84 is a 60-sample copy of the five-point arc: its deviation from
    the chords is the sagitta of a chord spanning 30 degrees of a sine bump,
    under 3 mm, and it must not become an internal line."""
    path = tmp_path / "clo.dxf"
    _clo_style(path)
    pattern, report = read_dxf(path)
    (piece,) = pattern.panels
    assert report.validation_curves == 2
    assert 0.2 < report.qv_deviation_mm < 3.0
    assert piece.meta["qv_deviation_mm"] == pytest.approx(report.qv_deviation_mm, abs=1e-3)
    assert pattern.provenance["validation_curves"] == 2
    assert not any(len(i.points) > 10 for i in piece.internals), "a QV curve was imported"


def test_units_come_from_the_argument_then_insunits_then_the_header(tmp_path) -> None:
    metric, english, bare = tmp_path / "m.dxf", tmp_path / "e.dxf", tmp_path / "b.dxf"
    _clo_style(metric)
    _clo_style(english, units="ENGLISH")
    _clo_style(bare, units=None)

    forced, report = read_dxf(metric, units_mm=1.0)
    assert report.units_source == "units_mm argument"
    assert forced.panels[0].bbox[2] == pytest.approx(40.0)

    inches, report = read_dxf(english)
    assert report.units_source == "header UNITS: ENGLISH"
    assert inches.panels[0].bbox[2] == pytest.approx(40.0 * 25.4)

    plain, report = read_dxf(bare)
    assert report.units_source == "undeclared; read as mm"
    assert plain.panels[0].bbox[2] == pytest.approx(40.0)
    assert plain.provenance["insunits_note"] == "0 = undeclared"

    _clo_style(tmp_path / "f.dxf", units="FURLONGS")
    with pytest.raises(ValueError, match="units_mm"):
        read_dxf(tmp_path / "f.dxf")
    with pytest.raises(ValueError, match="units_mm"):
        read_dxf(metric, units_mm=0.0)


def test_an_implausible_size_is_noted_not_hidden(tmp_path) -> None:
    path = tmp_path / "clo.dxf"
    _clo_style(path)
    _, report = read_dxf(path, units_mm=0.1)  # a 6 mm front
    assert report.notes and "units_mm" in report.notes[0]
    _, report = read_dxf(path, units_mm=100.0)  # a 6 m front
    assert report.notes and "6600 mm" in report.notes[0]


def test_two_boundaries_in_one_block_keep_the_largest_and_say_so(tmp_path) -> None:
    path = tmp_path / "clo.dxf"
    _clo_style(path, extra_boundary=True)
    pattern, report = read_dxf(path)
    assert pattern.panels[0].area_mm2 > 200_000.0
    assert report.notes == ["block Frente_M: 2 boundary polylines; the largest is the piece"]


def test_a_kept_sew_line_makes_the_boundary_the_cut_line(tmp_path) -> None:
    """seamkiln's own writer puts the cut line on layer 1 and the sew line on
    14; reading that back must not hand the cut line off as the piece."""
    original = tee_block()
    with_allowance = Pattern(
        name="tee", panels=[add_seam_allowance(p, 10.0) for p in original.panels], units="mm"
    )
    path = tmp_path / "tee_sa.dxf"
    assert write_dxf(with_allowance, path, flavour="astm")["entities"]["sew"] == 4
    back, report = read_dxf(path)
    assert report.units_source == "$INSUNITS 4"
    for piece in original.panels:
        got = back.panel(piece.id)
        assert got.meta["outline_is"] == "cut_line"
        assert got.seam_allowance_mm == pytest.approx(10.0, abs=0.01)
        assert got.area_mm2 > piece.area_mm2
        assert sum(1 for i in got.internals if i.kind is LineKind.SEW and i.closed) == 1
        from seamkiln.pattern.geometry import area

        assert area(sew_line(got)) == pytest.approx(piece.area_mm2, rel=1e-6)
