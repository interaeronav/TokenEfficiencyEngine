"""The critic must find real faults, and must not invent any."""

from __future__ import annotations

import pytest

from drafting import standards as S
from drafting.critic import critique, critique_sheet
from drafting.okongo import as_issued
from drafting.spec import DrawingSet, Line, Marker, Room, Sheet, Text, TitleBlock, View


def codes(report) -> set[str]:
    return {f.rule for f in report.findings}


def clean_sheet() -> Sheet:
    return Sheet(
        number="A-200",
        title="GROUND FLOOR PLAN",
        subtitle="",
        views=[
            View(
                "ga_plan",
                "plan",
                50,
                north_point=True,
                dimension_chains=list(S.DIMENSION_CHAINS),
                rooms=[Room("01", "BEDROOM")],
            )
        ],
        texts=[Text("title", 5.0), Text("dimension", 2.5), Text("note", 2.5)],
        lines=[Line("border", 0.70), Line("cut_secondary", 0.50), Line("hatch", 0.18)],
        title_block=TitleBlock(
            fields=dict.fromkeys(S.TITLE_BLOCK_FIELDS, "x"), notes=[S.DO_NOT_SCALE]
        ),
        provenance="tape survey",
    )


def test_a_conforming_sheet_produces_no_findings():
    """A critic that always complains is a critic nobody reads."""
    assert critique_sheet(clean_sheet()).findings == []


def test_text_below_the_minimum_is_caught():
    sheet = clean_sheet()
    sheet.texts.append(Text("note", 1.8))
    assert "TEXT-MIN" in codes(critique_sheet(sheet))


def test_a_border_drawn_light_is_caught():
    sheet = clean_sheet()
    sheet.lines[0] = Line("border", 0.25)
    assert "BORDER-WEIGHT" in codes(critique_sheet(sheet))


def test_one_line_weight_is_flagged_as_unreadable():
    sheet = clean_sheet()
    sheet.lines = [Line("border", 0.70), Line("cut_secondary", 0.70)]
    assert "LINE-HIERARCHY" in codes(critique_sheet(sheet))


def test_an_invented_scale_is_rejected():
    sheet = clean_sheet()
    sheet.views[0].scale_denominator = 75
    report = critique_sheet(sheet)
    assert "SCALE-PREFERRED" in codes(report)
    assert report.blocking


def test_a_plan_without_a_north_point_is_rejected():
    sheet = clean_sheet()
    sheet.views[0].north_point = False
    report = critique_sheet(sheet)
    assert "NORTH-POINT" in codes(report)
    assert report.blocking


def test_a_room_with_a_number_but_no_name_is_caught():
    sheet = clean_sheet()
    sheet.views[0].rooms = [Room("01", "")]
    assert "ROOM-ID" in codes(critique_sheet(sheet))


def test_levels_without_a_datum_are_caught():
    sheet = clean_sheet()
    sheet.views[0].levels = ["FFL ±0.000"]
    sheet.level_datum = ""
    assert "LEVEL-DATUM" in codes(critique_sheet(sheet))


def test_the_do_not_scale_note_is_required():
    sheet = clean_sheet()
    sheet.title_block.notes = []
    assert "DO-NOT-SCALE" in codes(critique_sheet(sheet))


def test_an_orphan_section_is_rejected():
    """A section drawn with no cut line on any plan. This is the defect the
    first issue of the Okongo set actually shipped with."""
    plan = clean_sheet()
    section = Sheet(
        number="A-400",
        title="SECTIONS",
        subtitle="",
        views=[View("ga_section", "SECTION A-A", 50)],
        texts=plan.texts,
        lines=plan.lines,
        title_block=plan.title_block,
        provenance="x",
    )
    report = critique(DrawingSet([plan, section]))
    assert "SECTION-ON-PLAN" in codes(report)
    assert report.blocking


def test_a_section_with_its_cut_line_drawn_is_accepted():
    plan = clean_sheet()
    plan.markers = [Marker(tag="A", target_sheet="A-400", drawn_on="A-200")]
    section = Sheet(
        number="A-400",
        title="SECTIONS",
        subtitle="",
        views=[View("ga_section", "SECTION A-A", 50)],
        texts=plan.texts,
        lines=plan.lines,
        title_block=plan.title_block,
        provenance="x",
    )
    assert "SECTION-ON-PLAN" not in codes(critique(DrawingSet([plan, section])))


def test_a_marker_pointing_at_a_sheet_that_is_not_in_the_set_is_rejected():
    plan = clean_sheet()
    plan.markers = [Marker(tag="A", target_sheet="A-999", drawn_on="A-200")]
    report = critique(DrawingSet([plan]))
    assert "MARKER-TARGET" in codes(report)


def test_the_okongo_set_as_issued_had_real_faults():
    """The record of what actually went out on 2026-09-03, kept as a test so
    the loop can never quietly stop finding them."""
    report = critique(as_issued())
    assert len(report) > 50
    assert "SECTION-ON-PLAN" in codes(report)
    assert "TEXT-MIN" in codes(report)
    assert "DO-NOT-SCALE" in codes(report)
    assert len(report.blocking) == 2, "both sections were orphans"


@pytest.mark.parametrize(
    "name,expected",
    [
        ("SECTION A-A", "A"),
        ("SECTION B\u2013B", "B"),
        ("Section c-c", "C"),
        ("DETAIL 1", "1"),
    ],
)
def test_section_tags_normalise_the_same_way_for_both_sides(name, expected):
    """The critic reading 'A-A' while the corrector wrote 'A' let two REJECT
    findings survive a loop that reported itself converged."""
    assert S.section_tag(name) == expected
