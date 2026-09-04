"""The Okongo as-scanned set, as data.

`as_issued()` describes the three sheets exactly as they were sent on
2026-09-03, measured off the composer that drew them (matplotlib points
converted at 1 pt = 0.352778 mm). It is deliberately an honest record of what
went out, so the critic has something real to fail.
"""

from __future__ import annotations

from drafting.spec import DrawingSet, Room, Sheet, Text, TitleBlock, View

PT = 0.352777778


def t(role: str, points: float, content: str = "") -> Text:
    return Text(role=role, height_mm=round(points * PT, 3), content=content)


def _common_title_block() -> TitleBlock:
    return TitleBlock(
        fields={
            "project": "Okongo Oneleiwa",
            "scale": "1:25 @ A3",
            "date": "2026-09-03",
        }
    )


def as_issued() -> DrawingSet:
    from drafting.spec import Line

    def base_lines(border_pt=1.2):
        return [
            Line("border", round(border_pt * PT, 3)),
            Line("hatch", round(0.5 * PT, 3)),  # grid
            Line("hatch", round(0.4 * PT, 3)),  # extension lines
            Line("fitting", round(0.85 * PT, 3)),  # dimension lines
        ]

    def base_texts():
        return [
            t("title", 16),
            t("subtitle", 7.4),
            t("grid", 11),
            t("note", 8.0),
            t("note", 6.0),
            t("note", 6.3),
            t("note", 7.4),
            t("note", 5.6),
            t("note", 6.0),
        ]

    sk01 = Sheet(
        number="SK-01",
        title="FLOOR PLAN — as-scanned survey",
        subtitle="Horizontal section at +1.200 m above finished floor",
        views=[
            View(
                kind="ga_plan",
                name="floor plan",
                scale_denominator=25,
                north_point=True,
                dimension_chains=["overall", "grid"],
                rooms=[Room("ROOM 01", "", 11.4), Room("ROOM 02", "", 5.1)],
            )
        ],
        texts=[
            *base_texts(),
            t("dimension", 7.2),
            t("note", 9.0),
            t("note", 6.6),
            t("note", 6.2),
            t("note", 6.1),
        ],
        lines=[
            *base_lines(),
            Line("cut_secondary", round(3.2 * PT, 3)),
            Line("beyond", round(2.2 * PT, 3)),
            Line("fitting", round(1.4 * PT, 3)),
        ],
        markers=[],  # <- none drawn, yet SK-02 cites them
        title_block=_common_title_block(),
    )

    sk02 = Sheet(
        number="SK-02",
        title="SECTIONS — as-scanned survey",
        subtitle="Vertical sections on a 120 mm band",
        views=[
            View(
                kind="ga_section",
                name="SECTION A-A",
                scale_denominator=50,
                levels=["FFL ±0.000", "SOFFIT +2.604"],
            ),
            View(
                kind="ga_section",
                name="SECTION B-B",
                scale_denominator=50,
                levels=["FFL ±0.000", "SOFFIT +2.604"],
            ),
        ],
        texts=[*base_texts(), t("dimension", 7.0), t("note", 6.3), t("note", 5.8), t("note", 6.2)],
        lines=base_lines(),
        title_block=_common_title_block(),
        level_datum="",  # <- never stated
    )

    sk03 = Sheet(
        number="SK-03",
        title="THREE-DIMENSIONAL VIEWS — as-scanned survey",
        subtitle="Z-buffered renders of the point cloud",
        views=[View(kind="pictorial", name="axonometrics", scale_denominator=0)],
        texts=[*base_texts(), t("note", 6.3), t("note", 8.0), t("note", 6.2)],
        lines=base_lines(),
        title_block=TitleBlock(fields={}),  # <- SK-03 has no title block at all
    )
    return DrawingSet([sk01, sk02, sk03])
