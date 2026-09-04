"""The loop must converge, must not fabricate, and must actually fix things."""

from __future__ import annotations

from drafting import loop
from drafting import standards as S
from drafting.corrector import UNSET, correct
from drafting.critic import critique
from drafting.okongo import as_issued

INPUTS = dict(
    project={
        "project": "Okongo Oneleiwa",
        "client": "J. Nangolo (owner)",
        "scale": "",
        "date": "2026-09-04",
        "drawn_by": "TEE pc_* lane (A67)",
        "checked_by": "",
    },
    rooms={"ROOM 01": "BEDROOM", "ROOM 02": "EN-SUITE / STORE"},
    cuts={"A": ("SK-01", 270.0), "B": ("SK-01", 180.0)},
    provenance="iPhone LiDAR, 1,520,736 points. SCALE UNVERIFIED.",
)


def test_the_loop_clears_the_blocking_findings():
    dset = as_issued()
    assert critique(dset).blocking, "the set as issued had blocking faults"
    loop.run(dset, **INPUTS)
    assert critique(dset).blocking == []


def test_the_loop_converges_rather_than_running_to_the_cap():
    dset = as_issued()
    result = loop.run(dset, **INPUTS)
    assert result.converged
    assert len(result.passes) < loop.MAX_PASSES


def test_the_loop_reaches_a_fixed_point():
    """A second run must find nothing left to do."""
    dset = as_issued()
    loop.run(dset, **INPUTS)
    again = correct(dset, **INPUTS)
    assert again.findings == []


def test_every_change_is_reported():
    dset = as_issued()
    before = len(critique(dset))
    result = loop.run(dset, **INPUTS)
    assert len(result.changes) >= before - len(result.remaining)
    assert all(f.autofixed for f in result.changes)


def test_the_corrector_does_not_invent_a_checker():
    """An unchecked drawing that looks checked is worse than one that does not.

    The corrector is given an empty `checked_by` and must leave it visibly
    unset rather than filling in a plausible name.
    """
    dset = as_issued()
    loop.run(dset, **INPUTS)
    for sheet in dset.sheets:
        assert sheet.title_block.fields["checked_by"] == UNSET


def test_corrections_snap_text_up_never_down_below_the_minimum():
    dset = as_issued()
    loop.run(dset, **INPUTS)
    for sheet in dset.sheets:
        for text in sheet.texts:
            assert text.height_mm >= S.TEXT_MIN_MM
            assert any(abs(text.height_mm - h) < 1e-6 for h in S.TEXT_HEIGHTS_MM)


def test_corrections_put_every_line_on_the_standard_pen_set():
    dset = as_issued()
    loop.run(dset, **INPUTS)
    for sheet in dset.sheets:
        for line in sheet.lines:
            assert any(abs(line.width_mm - w) < 1e-6 for w in S.LINE_WEIGHTS_MM)
        border = next(line for line in sheet.lines if line.role == "border")
        assert border.width_mm >= 0.70


def test_the_orphan_sections_get_their_cut_lines_drawn_on_the_plan():
    dset = as_issued()
    assert dset.by_number("SK-01").markers == []
    loop.run(dset, **INPUTS)
    tags = {m.tag for m in dset.by_number("SK-01").markers}
    assert tags == {"A", "B"}
    assert all(m.target_sheet == "SK-02" for m in dset.by_number("SK-01").markers)


def test_the_ga_plan_scale_is_brought_to_a_plan_scale():
    dset = as_issued()
    assert dset.by_number("SK-01").views[0].scale_denominator == 25
    loop.run(dset, **INPUTS)
    assert dset.by_number("SK-01").views[0].scale_denominator in S.SCALE_FOR_KIND["ga_plan"]
