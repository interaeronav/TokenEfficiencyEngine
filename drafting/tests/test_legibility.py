"""The plot tier: catch what the spec tier cannot see, and nothing else.

Every test here corresponds to a false positive or a miss found while running
the tier against a real sheet. A critic is only useful if its findings are
worth reading, so the false positives are pinned as hard as the misses.
"""

from __future__ import annotations

import pytest

matplotlib = pytest.importorskip("matplotlib")

from drafting import standards as S  # noqa: E402
from drafting.compose import SheetCanvas  # noqa: E402
from drafting.legibility import inspect, patch_boxes, text_boxes  # noqa: E402
from drafting.spec import Line, Sheet, Text, TitleBlock  # noqa: E402


def blank() -> Sheet:
    return Sheet(
        number="T-01",
        title="TEST",
        subtitle="",
        texts=[Text("title", 5.0), Text("note", 2.5)],
        lines=[Line("border", 0.70), Line("cut_primary", 0.70), Line("hatch", 0.18)],
        title_block=TitleBlock(fields={}, notes=[]),
    )


def canvas_with(body) -> SheetCanvas:
    canvas = SheetCanvas(blank())
    canvas.frame()
    body(canvas)
    return canvas


def test_overlapping_text_is_caught():
    def body(c):
        c.text(100, 150, "AAAAAAAAAAAA", "title")
        c.text(100, 150, "BBBBBBBBBBBB", "title")

    report = inspect(canvas_with(body))
    assert any(f.rule == "LEGIBILITY-OVERLAP" for f in report.findings)


def test_well_separated_text_is_not_caught():
    def body(c):
        c.text(40, 200, "LEFT", "note")
        c.text(300, 60, "RIGHT", "note")

    assert [f for f in inspect(canvas_with(body)).findings if f.rule == "LEGIBILITY-OVERLAP"] == []


def test_text_outside_the_frame_is_rejected():
    def body(c):
        c.text(2, 150, "OUTSIDE", "note")

    report = inspect(canvas_with(body))
    assert any(f.rule == "LEGIBILITY-FRAME" for f in report.findings)
    assert report.blocking


def test_a_line_through_unmasked_text_is_caught():
    def body(c):
        ax, _, _ = c.view_axes(40, 40, ((0, 0), (4, 3)), 50)
        ax.plot([0, 4], [1.5, 1.5], lw=2.0, color="k")
        ax.text(2, 1.5, "CROSSED", ha="center", va="center", fontsize=8)

    assert any(
        f.rule == "LEGIBILITY-OVERLAP" and "graphic" in f.where
        for f in inspect(canvas_with(body)).findings
    )


def test_a_line_under_MASKED_text_is_not_caught():
    """A dimension figure sits in a break in its own dimension line. Flagging
    that would make the tier fire on every correctly-drawn dimension."""

    def body(c):
        ax, _, _ = c.view_axes(40, 40, ((0, 0), (4, 3)), 50)
        ax.plot([0, 4], [1.5, 1.5], lw=2.0, color="k")
        ax.text(
            2,
            1.5,
            "1949",
            ha="center",
            va="center",
            fontsize=8,
            bbox=dict(fc="white", ec="none", pad=1.2),
        )

    assert [f for f in inspect(canvas_with(body)).findings if "graphic" in f.where] == []


def test_an_annotation_leader_is_not_treated_as_a_giant_text_box():
    """Annotation.get_window_extent includes the arrow: a 2 mm label with a
    35 mm leader once measured 35 mm tall and collided with everything near it."""

    def body(c):
        ax, _, _ = c.view_axes(40, 40, ((0, 0), (4, 3)), 50)
        ax.annotate(
            "TAG", xy=(3.5, 0.2), xytext=(0.4, 2.6), fontsize=7, arrowprops=dict(arrowstyle="->")
        )
        ax.text(2.0, 1.4, "MIDDLE", ha="center", fontsize=7)

    boxes = {b.label: b for b in text_boxes(canvas_with(body))}
    assert boxes["TAG"].y1 - boxes["TAG"].y0 < 6.0, "measured the leader, not the glyphs"


def test_an_axes_background_is_not_reported_as_covering_its_own_contents():
    """Counting Axes backgrounds made the whole plan one giant collision."""

    def body(c):
        ax, _, _ = c.view_axes(40, 40, ((0, 0), (4, 3)), 50)
        ax.text(2, 1.5, "INSIDE", ha="center", fontsize=8)

    assert not any("filled rectangle" in f.detail for f in inspect(canvas_with(body)).findings)


def test_a_filled_panel_over_text_is_caught():
    def body(c):
        c.text(60, 60, "BURIED", "note")
        c.fig.add_artist(
            matplotlib.pyplot.Rectangle(
                c.F(50, 55), 40 / c.w, 12 / c.h, fc="black", transform=c.fig.transFigure
            )
        )

    assert any("filled rectangle" in f.detail for f in inspect(canvas_with(body)).findings)


def test_the_composer_plots_at_the_scale_it_claims():
    """1:50 must mean 1 m of building = 20 mm of paper, or the scale bar lies."""
    canvas = SheetCanvas(blank())
    _, aw, ah = canvas.view_axes(30, 30, ((0.0, 0.0), (5.0, 4.0)), 50)
    assert aw == pytest.approx(100.0)
    assert ah == pytest.approx(80.0)


def test_patch_boxes_ignores_the_figure_background():
    canvas = canvas_with(lambda c: None)
    assert all(b.x1 - b.x0 < 0.9 * canvas.w for b in patch_boxes(canvas))


def test_points_and_millimetres_convert_the_way_the_standard_assumes():
    assert pytest.approx(7.087, abs=0.01) == S.POINTS_PER_MM * 2.5
