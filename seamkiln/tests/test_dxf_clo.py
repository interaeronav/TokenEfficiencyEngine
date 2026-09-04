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

The writer half was measured the same day and was worse: it wrote R2000
with both layout blocks, which is precisely the file Gerber Technology's
parser refuses, and its docstring claimed the blocks could not be removed.
`ezdxf.addons.gerber_D6673` removes them. The tests below read the BYTES of
what we write, because every claim here is about what somebody else's
program will see - and they hold the Style System Text, which is the only
place an R12 file can put its unit.
"""

from __future__ import annotations

import math

import ezdxf
import pytest

from seamkiln.pattern.allowance import add_seam_allowance, sew_line
from seamkiln.pattern.dxf import DxfDialectError, read_dxf, write_dxf
from seamkiln.pattern.fixtures import tee_block
from seamkiln.pattern.geometry import Vertex, VertexKind
from seamkiln.pattern.model import LineKind, MarkKind, Panel, Pattern

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
    assert report.units_source == "header UNITS: METRIC"
    for piece in original.panels:
        got = back.panel(piece.id)
        assert got.meta["outline_is"] == "cut_line"
        assert got.seam_allowance_mm == pytest.approx(10.0, abs=0.01)
        assert got.area_mm2 > piece.area_mm2
        assert sum(1 for i in got.internals if i.kind is LineKind.SEW and i.closed) == 1
        from seamkiln.pattern.geometry import area

        assert area(sew_line(got)) == pytest.approx(piece.area_mm2, rel=1e-6)


# -- what we write, read as bytes by the far end ------------------------------


def _sections(path) -> list[str]:
    """The DXF section names, straight off the file."""
    lines = [line.strip() for line in path.read_text(encoding="ascii").splitlines()]
    return [lines[i + 2] for i, line in enumerate(lines) if line == "SECTION"]


def test_the_written_file_is_the_shape_gerber_can_parse(tmp_path) -> None:
    """The defect, held: `write_dxf` wrote AC1015 with `*Model_Space` and
    `*Paper_Space` in it, and Gerber's parser rejects exactly that. The
    add-on ezdxf ships for this (`gerber_D6673`) strips the layout blocks,
    the TABLES section and the header, which is why R12 is the default."""
    path = tmp_path / "gerber.dxf"
    report = write_dxf(tee_block(), path, flavour="astm")
    assert report["dxfversion"] == "R12" and report["gerber_safe"] is True
    assert report["layout_blocks_present"] == []

    raw = path.read_bytes()
    assert raw.isascii(), "D6673 is 7-bit ASCII"
    text = raw.decode("ascii")
    assert "*Model_Space" not in text and "*Paper_Space" not in text
    assert _sections(path) == ["HEADER", "BLOCKS", "ENTITIES"], "no TABLES, and one empty HEADER"
    assert "$INSUNITS" not in text, "R12 exports none; the unit is the SST"
    assert ezdxf.readfile(path).dxfversion == "AC1009"


def test_the_unit_survives_r12_in_the_mandatory_style_system_text(tmp_path) -> None:
    """R12 carries no `$INSUNITS`, so an R12 file with no SST would declare
    no unit at all and this reader would fall back to "millimetres, with a
    note" - a regression dressed as a fix. The SST is mandatory in the
    standard and is what both real CLO exports carry; `UNITS: METRIC` is
    centimetres, so the geometry is written in centimetres to match it."""
    path = tmp_path / "sst.dxf"
    write_dxf(tee_block(), path, flavour="astm")
    pattern, report = read_dxf(path)

    assert report.insunits == 0
    assert report.units_source == "header UNITS: METRIC", "the fallback is silent millimetres"
    assert report.scale_mm == 10.0
    assert list(report.header) == [
        "STYLE NAME",
        "CREATION DATE",
        "CREATION TIME",
        "AUTHOR",
        "PRODUCT",
        "VERSION",
        "UNITS",
    ], "the SST keys, in the order the two CLO exports write them"
    assert report.header["AUTHOR"] == "seamkiln"
    assert pattern.name == "tee-block", "STYLE NAME carries the style's name back"

    # on layer 1, with the boundary, where the standard puts it
    space = ezdxf.readfile(path).modelspace()
    sst = [e for e in space if e.dxftype() == "TEXT"]
    assert len(sst) == 7 and {e.dxf.layer for e in sst} == {"1"}
    # and the numbers in the file really are centimetres, not millimetres
    front = tee_block().panel("FRONT")
    block = ezdxf.readfile(path).blocks.get("FRONT")
    boundary = next(e for e in block if e.dxftype() == "POLYLINE" and e.dxf.layer == "1")
    drawn = max(v.dxf.location.x for v in boundary.vertices)
    assert drawn == pytest.approx(front.bbox[2] / 10.0, abs=1e-9)


def test_a_style_read_from_cad_keeps_its_sample_size_when_written_back(tmp_path) -> None:
    """SAMPLE SIZE is a fact about the style, not about seamkiln, so it is
    carried across a round trip rather than restamped or dropped."""
    source, out = tmp_path / "clo.dxf", tmp_path / "again.dxf"
    _clo_style(source)
    pattern, _ = read_dxf(source)
    write_dxf(pattern, out, flavour="astm")
    _, report = read_dxf(out)
    assert report.header["SAMPLE SIZE"] == "M"
    assert report.header["STYLE NAME"] == "Camiseta"
    assert report.header["AUTHOR"] == "seamkiln", "we wrote this file, so we sign it"


def test_a_name_ascii_7_cannot_carry_is_named_not_lost(tmp_path) -> None:
    """D6673 is ASCII-7 and the export enforces it. An accent survives as an
    escape that does not decode back, so the writer reports the strings it
    had to escape instead of letting a piece quietly change its name."""
    outline = [Vertex(0, 0), Vertex(400, 0), Vertex(0, 600)]
    panel = Panel(id="Frente", name="Frênte", outline=outline)
    report = write_dxf(Pattern(name="Calça", panels=[panel]), tmp_path / "a.dxf", flavour="astm")
    # Title Case: the standard's form, and Optitex's. See `_style_system_text`.
    assert report["non_ascii_escaped"] == ["Style Name: Calça", "Piece Name: Frênte"]
    assert (tmp_path / "a.dxf").read_bytes().isascii()

    plain = write_dxf(tee_block(), tmp_path / "b.dxf", flavour="astm")
    assert plain["non_ascii_escaped"] == []


def test_r2000_is_the_opt_out_and_declares_the_same_size(tmp_path) -> None:
    """Kept for a generic CAD viewer that wants a header and a layer table.
    It is not interchange and says so, and it carries the same centimetre
    geometry, so the two versions can never disagree about how big a piece
    is: `$INSUNITS 5` is centimetres, which is what the SST already said."""
    path = tmp_path / "viewer.dxf"
    report = write_dxf(tee_block(), path, flavour="astm", version="R2000")
    assert report["gerber_safe"] is False
    assert report["layout_blocks_present"] == ["*Model_Space", "*Paper_Space"]
    assert ezdxf.readfile(path).dxfversion == "AC1015"
    # the report is not taking our word for it: they really are in the file,
    # which is exactly why Gerber cannot read this one
    text = path.read_text(encoding="utf-8")
    assert "*Model_Space" in text and "*Paper_Space" in text
    assert "TABLES" in text and "$INSUNITS" in text

    back, read = read_dxf(path)
    assert read.units_source == "$INSUNITS 5" and read.scale_mm == 10.0
    for piece in tee_block().panels:
        assert back.panel(piece.id).area_mm2 == pytest.approx(piece.area_mm2, rel=1e-9)


# -- the layers we cannot name, and the ones we have now witnessed ------------


def _with_stray_layers(path) -> None:
    """Two pieces, each carrying two layers NO dialect defines: 12 as points
    and 16 as a closed polyline.

    12 and 16 are in neither the ASTM nor the AAMA table, which is the point
    - a layer the table defines but no real file has ever exercised (13, 14,
    82 ...) is a different thing entirely and must not be reported as this.
    """
    doc = ezdxf.new("R12")
    space = doc.modelspace()
    space.add_text("UNITS: METRIC", dxfattribs={"layer": "1", "height": 1.0})
    for piece in ("A", "B"):
        block = doc.blocks.new(piece)
        block.add_polyline2d(CORNERS, close=True, dxfattribs={"layer": "1"})
        block.add_point((5.0, 5.0), dxfattribs={"layer": "12"})
        block.add_point((6.0, 6.0), dxfattribs={"layer": "12"})
        block.add_polyline2d(
            [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0)], close=True, dxfattribs={"layer": "16"}
        )
        space.add_blockref(piece, (0.0, 0.0))
    doc.saveas(path)


def test_an_unknown_layer_refuses_by_what_it_holds_and_asks(tmp_path) -> None:
    """A tally cannot tell anyone what a layer IS, and ten of the eighteen
    ASTM layers have never been seen in a real file - so the refusal has to
    hand back enough for a pattern maker to answer from their own screen."""
    path = tmp_path / "strays.dxf"
    _with_stray_layers(path)
    with pytest.raises(DxfDialectError) as excinfo:
        read_dxf(path, flavour="astm")
    message = str(excinfo.value)
    assert "layer 12 holds 4 POINT across 2 pieces" in message
    assert "layer 16 holds 2 POLYLINE (2 closed) across 2 pieces" in message
    assert "will not guess" in message, "the design is that we refuse and ask"
    assert "strict=False" in message  # the way out is named, not just the wall


def test_lenient_reading_keeps_the_census_and_says_what_it_dropped(tmp_path) -> None:
    """Leniency that stays quiet teaches nobody: a caller who skipped a layer
    should still come away knowing what was on it."""
    path = tmp_path / "strays.dxf"
    _with_stray_layers(path)
    pattern, report = read_dxf(path, flavour="astm", strict=False)

    assert len(pattern.panels) == 2
    assert report.unknown_layers == {
        "12": {"entities": {"POINT": 4}, "pieces": 2},
        "16": {"entities": {"POLYLINE": 2}, "pieces": 2, "closed": 2},
    }
    assert len(report.notes) == 1
    note = report.notes[0]
    assert "layer 12 holds 4 POINT across 2 pieces" in note
    assert "layer 16 holds 2 POLYLINE (2 closed) across 2 pieces" in note
    assert "unknown_layers" in note
    # and nothing was promoted into the pattern on a guess
    assert all(not piece.marks and not piece.internals for piece in pattern.panels)


def test_a_file_says_which_defined_layers_it_exercised(tmp_path) -> None:
    """The evidence a future claim of field verification would rest on. The
    two real CLO 2024 exports exercise these same eight of the eighteen ASTM
    layers (measured 2026-09-04); the other ten are defined from a published
    description and unwitnessed - which is NOT the same as unknown, and this
    holds the two apart."""
    path = tmp_path / "clo.dxf"
    _clo_style(path)
    pattern, report = read_dxf(path)

    assert report.observed_layers == ["1", "2", "3", "4", "7", "8", "84", "85"]
    assert report.unknown_layers == {}, "a defined layer is never an unknown one"
    assert pattern.provenance["observed_layers"] == report.observed_layers

    unwitnessed = {"5", "6", "9", "10", "11", "13", "14", "82", "86", "87"}
    assert unwitnessed.isdisjoint(report.observed_layers)
    assert unwitnessed.isdisjoint(report.unknown_layers)


def test_the_stray_layers_of_one_dialect_are_the_other_s_own(tmp_path) -> None:
    """AAMA defines no quality-validation layers, so the same CLO file read
    as AAMA reports 84 and 85 as unknown - with their contents, which is
    exactly the census that would let someone confirm what they are."""
    path = tmp_path / "clo.dxf"
    _clo_style(path)
    _, report = read_dxf(path, flavour="aama", strict=False)
    assert sorted(report.unknown_layers) == ["84", "85"]
    assert report.unknown_layers["84"] == {
        "entities": {"POLYLINE": 1},
        "pieces": 1,
        "closed": 1,
    }
    assert report.unknown_layers["85"] == {"entities": {"POLYLINE": 1}, "pieces": 1}
    assert report.observed_layers == ["1", "2", "3", "4", "7", "8"]


# -- the control piece: ground truth by construction --------------------------


def _with_control_piece(
    path,
    *,
    label: str = '10"X10"',
    insunits: int | None = 6,
    square: bool = True,
    name: str = "CONTROL PIECE",
    category: str = "DO NOT CUT",
) -> None:
    """One garment piece and one scale square, in inches, under a header that
    LIES - the shape of the purchased Optitex AAMA block measured 2026-09-04,
    which declares `$INSUNITS 6` (metres) and draws in inches.

    The garment piece is 36.622 units wide, exactly as that file's dress
    front is, so a correct read returns 930.2 mm and a credulous one returns
    36,622 mm.
    """
    doc = ezdxf.new("R2000")
    # ezdxf.new() stamps $INSUNITS 6 of its own accord, so "declares nothing"
    # has to be written explicitly as 0 - which is what "unitless" means
    doc.header["$INSUNITS"] = 0 if insunits is None else insunits
    space = doc.modelspace()
    space.add_text("Author: Optitex", dxfattribs={"layer": "1", "height": 0.25})

    front = doc.blocks.new("FRT")
    front.add_lwpolyline(
        [(0, 0), (36.622334, 0), (36.622334, 29.246332), (0, 29.246332)],
        close=True,
        dxfattribs={"layer": "1"},
    )
    front.add_text("Piece Name: dress FRT", dxfattribs={"layer": "1", "height": 0.25})
    space.add_blockref("FRT", (0, 0))

    control = doc.blocks.new("CTRL")
    wide, high = (10.0, 10.0) if square else (10.0, 6.0)
    control.add_lwpolyline(
        [(0, 0), (wide, 0), (wide, high), (0, high)], close=True, dxfattribs={"layer": "1"}
    )
    for line in (f"Piece Name: {name}", f"Category: {category}", f"Annotation: {label}"):
        control.add_text(line, dxfattribs={"layer": "1", "height": 0.25})
    space.add_blockref("CTRL", (0, 0))
    doc.saveas(path)


def test_a_control_piece_outranks_a_header_that_lies(tmp_path) -> None:
    """The purchased Optitex block declares metres and draws in inches. A
    header field is a claim; the control square is a measurement, so it wins
    - and 39.37x of silent error becomes a number the caller can assert on."""
    path = tmp_path / "optitex.dxf"
    _with_control_piece(path)
    pattern, report = read_dxf(path, flavour="aama")

    assert report.scale_mm == 25.4
    assert report.insunits == 6, "the lie is still recorded, not scrubbed"
    assert report.units_source == "control piece 'CTRL' (10\"X10\")"
    assert report.control_piece == {
        "block": "CTRL",
        "label": '10"X10"',
        "drawn": [10.0, 10.0],
        "size_mm": [254.0, 254.0],
        "mm_per_unit": 25.4,
    }
    assert report.units_conflict == {
        "declared": "$INSUNITS 6",
        "declared_mm_per_unit": 1000.0,
        "measured_mm_per_unit": 25.4,
        "ratio": 39.3701,
        "won": "control piece",
    }
    assert pattern.provenance["units_conflict"] == report.units_conflict
    assert len(report.notes) == 1
    note = report.notes[0]
    assert "25.4 mm" in note and "1000.0 mm" in note and "39.37" in note

    # the number this whole rung exists for
    (front,) = pattern.panels
    assert front.bbox[2] - front.bbox[0] == pytest.approx(930.2, abs=0.05)


def test_a_control_piece_is_not_a_garment_panel(tmp_path) -> None:
    """DO NOT CUT means it: a scale square is metadata, and returning it as a
    panel would put a 254 mm square through arrange, drape and the cutter."""
    path = tmp_path / "optitex.dxf"
    _with_control_piece(path)
    pattern, report = read_dxf(path, flavour="aama")
    assert [p.id for p in pattern.panels] == ["FRT"]
    assert report.pieces == 1
    assert report.skipped_blocks == ["*Model_Space", "*Paper_Space", "CTRL"]


def test_an_unreadable_control_label_falls_through_with_a_note(tmp_path) -> None:
    """Inches and centimetres are 2.54 apart, so a size with no unit is never
    guessed at. It says what it saw and drops to the next rung - which here
    is the same lie the control piece would have caught, and that is honest:
    we did not understand the evidence, so we do not get to claim we did."""
    path = tmp_path / "vague.dxf"
    _with_control_piece(path, label="10X10")
    _, report = read_dxf(path, flavour="aama")

    assert report.units_source == "$INSUNITS 6"
    assert report.control_piece is None and report.units_conflict is None
    assert any("looks like a control piece" in n and "without guessing" in n for n in report.notes)


def test_a_control_piece_that_is_not_the_shape_it_claims_is_not_evidence(tmp_path) -> None:
    """A false positive here rescales a whole garment, so the drawn shape has
    to match the shape the label claims before the label sets the unit."""
    path = tmp_path / "oblong.dxf"
    _with_control_piece(path, square=False)
    _, report = read_dxf(path, flavour="aama")

    assert report.units_source == "$INSUNITS 6"
    assert report.control_piece is None
    assert any("1.667:1" in n and "1.000:1" in n for n in report.notes)


def test_a_metric_control_label_is_read_the_same_way(tmp_path) -> None:
    """`25 cm X 25 cm` on a square drawn 10 units across means 25 mm a unit.
    Only labels that state their unit are read; that is the whole rule."""
    path = tmp_path / "metric.dxf"
    _with_control_piece(path, label="25 cm X 25 cm", insunits=None)
    _, report = read_dxf(path, flavour="aama")
    assert report.scale_mm == pytest.approx(25.0)
    assert report.units_conflict is None, "nothing was declared, so nothing disagreed"


def test_a_control_piece_that_agrees_with_the_header_reports_no_conflict(tmp_path) -> None:
    """The happy case has to stay quiet: a file whose square confirms its own
    header is a good file, and saying so loudly would train people to ignore
    the note that matters."""
    path = tmp_path / "honest.dxf"
    _with_control_piece(path, insunits=1)  # 1 = inches, which is the truth here
    _, report = read_dxf(path, flavour="aama")
    assert report.scale_mm == 25.4
    assert report.units_conflict is None and report.notes == []


def test_an_explicit_units_mm_still_outranks_the_control_piece(tmp_path) -> None:
    """Rung 1 is the caller. Someone who states the unit has looked at the
    file, and nothing in it may overrule them."""
    path = tmp_path / "optitex.dxf"
    _with_control_piece(path)
    _, report = read_dxf(path, flavour="aama", units_mm=1.0)
    assert report.units_source == "units_mm argument" and report.scale_mm == 1.0
    assert report.control_piece is None
