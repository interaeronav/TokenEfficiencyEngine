"""Draw the sheet furniture to the corrected spec.

This module owns only what the standards govern - border, title block, notes,
scale bar, north point, section marks, text and line weights. What goes INSIDE
the frame is the project's business and is passed in as a callable, so the
standards-compliant frame is reusable and the drawing content is not smuggled
into a library that has no business knowing about point clouds.

Every size here is millimetres on the plotted sheet, which is the only unit in
which a drafting standard means anything.
"""

from __future__ import annotations

from collections.abc import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow

from drafting import standards as S
from drafting.spec import Sheet

INK = "#111111"
GREY = "#9aa0a6"
ACCENT = "#0b6e99"
MUTED = "#3c4043"
FAINT = "#e6e8eb"


def mm_to_points(mm: float) -> float:
    return mm * S.POINTS_PER_MM


class SheetCanvas:
    """A sheet you address in millimetres, with the frame already correct."""

    def __init__(self, sheet: Sheet):
        self.spec = sheet
        self.w, self.h = S.SHEET_SIZES_MM[sheet.size]
        if sheet.orientation == "portrait":
            self.w, self.h = self.h, self.w
        self.fig = plt.figure(figsize=(self.w / 25.4, self.h / 25.4), facecolor="white")
        self._weights = {line.role: line.width_mm for line in sheet.lines}
        self._heights = {t.role: t.height_mm for t in sheet.texts}

    # -- unit helpers ------------------------------------------------------
    def F(self, x: float, y: float) -> tuple[float, float]:
        return (x / self.w, y / self.h)

    def pen(self, role: str) -> float:
        return mm_to_points(self._weights.get(role, S.LINE_ROLE_MM.get(role, 0.25)))

    def type_size(self, role: str) -> float:
        return mm_to_points(self._heights.get(role, S.TEXT_ROLE_MM.get(role, 2.5)))

    def text(self, x, y, s, role="note", **kw):
        kw.setdefault("color", INK)
        kw.setdefault("va", "center")
        self.fig.text(
            *self.F(x, y), s, fontsize=self.type_size(role), transform=self.fig.transFigure, **kw
        )

    def rule(self, x0, y0, x1, y1, role="hatch", **kw):
        self.fig.add_artist(
            plt.Line2D(
                [x0 / self.w, x1 / self.w],
                [y0 / self.h, y1 / self.h],
                lw=self.pen(role),
                color=kw.pop("color", INK),
                transform=self.fig.transFigure,
                **kw,
            )
        )

    # -- the frame the standards actually govern ---------------------------
    def frame(self) -> None:
        m = 8.0
        self.fig.add_artist(
            plt.Rectangle(
                self.F(m, m),
                (self.w - 2 * m) / self.w,
                (self.h - 2 * m) / self.h,
                fill=False,
                ec=INK,
                lw=self.pen("border"),
                transform=self.fig.transFigure,
            )
        )
        self.rule(m, self.h - 30, self.w - m, self.h - 30, "cut_secondary")
        self.text(14, self.h - 18, self.spec.title, "title", weight="bold")
        self.text(14, self.h - 25, self.spec.subtitle, "subtitle", color=MUTED)
        self.text(
            self.w - 14,
            self.h - 18,
            f"{self.spec.number}  rev {self.spec.title_block.fields.get('revision', '')}",
            "grid",
            weight="bold",
            ha="right",
        )

    def title_block(self) -> None:
        tb = self.spec.title_block
        order = [
            "project",
            "client",
            "drawing_title",
            "drawing_number",
            "revision",
            "scale",
            "date",
            "drawn_by",
            "checked_by",
        ]
        rows = [(k, tb.fields.get(k, "")) for k in order]
        bw, bh = 132.0, 8.0 + len(rows) * 5.6 + 16.0
        x, y = self.w - bw - 14, 14.0
        self.fig.add_artist(
            plt.Rectangle(
                self.F(x, y),
                bw / self.w,
                bh / self.h,
                fill=False,
                ec=INK,
                lw=self.pen("cut_secondary"),
                transform=self.fig.transFigure,
            )
        )
        self.rule(x, y + bh - 8, x + bw, y + bh - 8, "beyond")
        self.text(x + 3, y + bh - 4, tb.fields.get("project", "").upper(), "note", weight="bold")
        for i, (key, value) in enumerate(rows):
            yy = y + bh - 13.5 - i * 5.6
            self.text(x + 3, yy, key.replace("_", " ").upper(), "note", color=MUTED)
            unset = value == "— NOT SET —"
            self.text(
                x + 42,
                yy,
                value or "—",
                "note",
                color=("#b03a2e" if unset else INK),
                weight=("bold" if unset else "normal"),
            )
        note_y = y + 11
        for note in tb.notes[:2]:
            self.text(x + 3, note_y, note, "note", weight="bold")
            note_y -= 5.2

    def revision_table(self) -> None:
        """Above the title block, newest first - where a reader looks for it."""
        rows = list(reversed(self.spec.revisions))[:4]
        if not rows:
            return
        bw, rh = 132.0, 5.2
        bh = 6.0 + len(rows) * rh
        x, y = self.w - bw - 14, 14.0 + 8.0 + 9 * 5.6 + 16.0 + 3.0
        self.fig.add_artist(
            plt.Rectangle(
                self.F(x, y),
                bw / self.w,
                bh / self.h,
                fill=False,
                ec=INK,
                lw=self.pen("title_block"),
                transform=self.fig.transFigure,
            )
        )
        self.text(x + 3, y + bh - 3.0, "REV", "note", weight="bold", color=MUTED)
        self.text(x + 16, y + bh - 3.0, "DATE", "note", weight="bold", color=MUTED)
        self.text(x + 40, y + bh - 3.0, "DESCRIPTION", "note", weight="bold", color=MUTED)
        self.text(x + 106, y + bh - 3.0, "BY", "note", weight="bold", color=MUTED)
        for i, rev in enumerate(rows):
            yy = y + bh - 3.0 - (i + 1) * rh
            self.text(x + 3, yy, rev.code, "note", weight="bold")
            self.text(x + 16, yy, rev.date, "note")
            self.text(x + 40, yy, rev.description[:46], "note")
            self.text(x + 106, yy, (rev.by or "-")[:14], "note")

    def notes_panel(self, x: float, y: float, lines: list[str]) -> None:
        for i, line in enumerate(lines):
            self.text(x, y - i * 4.6, line, "note", color=MUTED, family="monospace")

    def scale_bar(self, x: float, y: float, denominator: int, metres: int = 5) -> None:
        step = 1000.0 / denominator
        for i in range(metres):
            self.fig.add_artist(
                plt.Rectangle(
                    self.F(x + i * step, y),
                    step / self.w,
                    1.8 / self.h,
                    fc=(INK if i % 2 == 0 else "white"),
                    ec=INK,
                    lw=self.pen("hatch"),
                    transform=self.fig.transFigure,
                )
            )
        for i in range(metres + 1):
            self.text(x + i * step, y - 3.6, str(i), "note", ha="center")
        self.text(
            x + metres * step / 2,
            y + 4.8,
            f"metres — 1:{denominator}",
            "note",
            ha="center",
            color=MUTED,
        )

    def north_point(
        self,
        ax,
        x: float,
        y: float,
        r: float,
        bearing_deg: float = 0.0,
        basis: str = "SCAN",
    ) -> None:
        """`bearing_deg` turns the arrow clockwise from up the page, so a plan
        drawn for readability can still point at the real north.

        `basis` says where the direction CAME FROM, and is not decoration. An
        arrow taken from the dominant wall azimuth is a drawing convention; one
        a client named is their word; neither is a surveyed bearing, and a bare
        N claims to be one.
        """
        import numpy as _np

        rad = _np.deg2rad(bearing_deg)
        dx, dy = _np.sin(rad), _np.cos(rad)
        ax.add_patch(
            FancyArrow(
                x - dx * r,
                y - dy * r,
                2 * r * dx,
                2 * r * dy,
                width=r * 0.08,
                head_width=r * 0.42,
                head_length=r * 0.55,
                fc=INK,
                ec=INK,
                length_includes_head=True,
                zorder=9,
            )
        )
        # SCAN north, not true north. The direction comes from the dominant
        # wall azimuth the leveller removed: it is a drawing convention, and a
        # bare "N" on a survey drawing claims a bearing nobody measured.
        ax.text(
            x + dx * r * 1.45,
            y + dy * r * 1.45,
            "N",
            ha="center",
            va="bottom",
            zorder=9,
            fontsize=self.type_size("grid"),
            weight="bold",
            color=INK,
        )
        # Offset ACROSS the arrow, not along it: a long basis label placed
        # beyond the head runs back over the N when the arrow points sideways.
        ax.text(
            x + dx * r * 1.5 - dy * r * 1.1,
            y + dy * r * 1.5 + dx * r * 1.1,
            basis,
            ha="center",
            va="bottom",
            zorder=9,
            fontsize=self.type_size("note"),
            color=MUTED,
        )

    def section_mark(self, ax, tag: str, p1, p2, target: str) -> None:
        """A cut line with a direction of view and the sheet it lands on."""
        import numpy as np

        a, b = np.array(p1, float), np.array(p2, float)
        ax.plot(
            [a[0], b[0]],
            [a[1], b[1]],
            color=ACCENT,
            lw=self.pen("cut_primary"),
            ls=(0, (9, 3, 1.5, 3)),
            zorder=8,
        )
        direction = (b - a) / (np.linalg.norm(b - a) or 1.0)
        normal = np.array([-direction[1], direction[0]])
        for end, sign in ((a, 1.0), (b, -1.0)):
            tip = end + normal * 0.34
            ax.annotate(
                "",
                xy=tuple(tip),
                xytext=tuple(end),
                zorder=9,
                arrowprops=dict(
                    arrowstyle="-|>", color=ACCENT, lw=self.pen("beyond"), mutation_scale=8
                ),
            )
            ax.text(
                *(end + direction * sign * 0.30 + normal * 0.10),
                f"{tag}",
                color=ACCENT,
                fontsize=self.type_size("grid"),
                weight="bold",
                ha="center",
                va="center",
                zorder=9,
                bbox=dict(boxstyle="circle,pad=0.22", fc="white", ec=ACCENT, lw=self.pen("beyond")),
            )
        mid = (a + b) / 2 + normal * 0.42
        ax.text(
            mid[0],
            mid[1],
            f"{tag}\u2013{tag}  →  {target}",
            color=ACCENT,
            zorder=9,
            fontsize=self.type_size("note"),
            ha="center",
            bbox=dict(fc="white", ec="none", pad=1.0),
        )

    def view_axes(self, x: float, y: float, extent_m, denominator: int):
        """An axes placed and sized so the plotted scale is exactly 1:denominator."""
        (x0, y0), (x1, y1) = extent_m
        aw = (x1 - x0) * 1000.0 / denominator
        ah = (y1 - y0) * 1000.0 / denominator
        ax = self.fig.add_axes([x / self.w, y / self.h, aw / self.w, ah / self.h])
        ax.set_aspect("equal")
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.axis("off")
        return ax, aw, ah

    def save(self, *paths, dpi: int = 175) -> None:
        for path in paths:
            self.fig.savefig(path, dpi=dpi)
        plt.close(self.fig)


def compose(sheet: Sheet, body: Callable[[SheetCanvas], None]) -> SheetCanvas:
    canvas = SheetCanvas(sheet)
    canvas.frame()
    body(canvas)
    canvas.title_block()
    canvas.revision_table()
    return canvas
