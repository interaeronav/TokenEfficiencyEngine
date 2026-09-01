"""The tech pack: the document a factory is actually sent.

A garment that exists only as a mesh is a picture. What gets made is a spec:
the piece list with areas and cut counts, the fabric card WITH ITS TIER FLAG,
the measurements, the ease at each landmark, the seam schedule, and the
plotter sheet the pieces are cut from.

The tier flag travels into the document on purpose. A tech pack that prints a
bending stiffness as if it were measured, when it is a solver constant chosen
to look right, is worse than one that omits it: someone will cut cloth
against it.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

TITLE_SIZE = 16
HEAD_SIZE = 10
BODY_SIZE = 8


def _need_fpdf():
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError(
            "the tech pack needs fpdf2. Install seamkiln's [plot] extra "
            "(uv pip install 'seamkiln[plot]')."
        ) from exc
    return FPDF


def write(
    session: Any,
    out: str | Path,
    *,
    style: str = "",
    author: str = "",
    stamp: str | None = None,
) -> dict[str, Any]:
    """Write the tech pack. Returns a summary - never the document."""
    FPDF = _need_fpdf()
    if session.pattern is None or not session.pattern.panels:
        raise ValueError("there is no pattern to document. Draft one first.")

    from seamkiln.pattern.fabric import fabric as fabric_by_name
    from seamkiln.pattern.plot import piece_report

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(True, margin=18)
    pdf.set_title(style or session.name)
    if author:
        pdf.set_author(author)
    pdf.add_page()

    pdf.set_font("helvetica", "B", TITLE_SIZE)
    pdf.cell(0, 9, style or session.name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=BODY_SIZE)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(
        0,
        5,
        f"seamkiln tech pack  -  {stamp or date.today().isoformat()}"
        f"  -  {len(session.pattern.panels)} pieces, {len(session.pattern.seams)} seams",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    sections = 0

    # -- pieces
    _heading(pdf, "Pieces")
    _table(
        pdf,
        ["piece", "area cm2", "perimeter mm", "bbox mm", "notches", "drills", "SA mm"],
        [
            [
                row["name"],
                f"{row['area_mm2'] / 100:,.0f}",
                f"{row['perimeter_mm']:,.0f}",
                f"{row['bbox_mm'][0]:.0f} x {row['bbox_mm'][1]:.0f}",
                str(row["notches"]),
                str(row["drills"]),
                f"{row['seam_allowance_mm']:.0f}",
            ]
            for row in (piece_report(panel) for panel in session.pattern.panels)
        ],
        widths=[38, 24, 28, 30, 20, 18, 18],
    )
    sections += 1

    # -- fabric, with the tier flag
    cloth = fabric_by_name(session.fabric)
    _heading(pdf, "Fabric")
    _table(
        pdf,
        ["property", "value", "tier"],
        [
            ["name", cloth.name, str(cloth.tier)],
            ["weight", f"{cloth.gsm:.0f} g/m2", "published range"],
            ["thickness", f"{cloth.thickness_mm:.2f} mm", "published range"],
            [
                "tensile warp / weft",
                f"{cloth.tensile_warp:.2f} / {cloth.tensile_weft:.2f}",
                str(cloth.tier),
            ],
            [
                "bending warp / weft",
                f"{cloth.bend_warp:.2f} / {cloth.bend_weft:.2f}",
                str(cloth.tier),
            ],
            ["shear", f"{cloth.shear:.2f}", str(cloth.tier)],
            ["friction", f"{cloth.friction:.2f}", str(cloth.tier)],
        ],
        widths=[52, 62, 40],
    )
    pdf.set_font("helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0,
        4,
        "Tier `plausible` means a solver constant chosen to behave like the cloth, "
        "not a laboratory measurement. Replace with KES-F or fabric-kit output "
        "before cutting to these numbers.",
    )
    pdf.set_text_color(0, 0, 0)
    sections += 1

    # -- seams
    if session.pattern.seams:
        from seamkiln.pattern.model import true_up

        checks = {c.seam_id: c for c in true_up(session.pattern, tolerance_mm=0.0)}
        _heading(pdf, "Seam schedule")
        _table(
            pdf,
            ["seam", "from", "to", "ease", "mismatch mm"],
            [
                [
                    seam.id,
                    str(seam.a),
                    str(seam.b),
                    f"{(seam.gather - 1) * 100:+.1f}%",
                    f"{checks[seam.id].mismatch_mm:+.2f}" if seam.id in checks else "-",
                ]
                for seam in session.pattern.seams
            ],
            widths=[42, 34, 34, 22, 28],
        )
        sections += 1

    # -- fit, when there is a drape to report on
    if session.drape is not None and session.body is not None:
        verdict = session.drape.report()
        if not verdict.get("converged", True):
            _heading(pdf, "Fit - NOT CONVERGED")
            pdf.set_font("helvetica", "B", BODY_SIZE)
            pdf.set_text_color(170, 0, 0)
            pdf.multi_cell(
                0,
                4.5,
                "The drape behind these numbers has not converged: "
                + "; ".join(verdict.get("not_converged", []))
                + ". They are printed for reference and must not be cut against.",
            )
            pdf.set_text_color(0, 0, 0)
        from seamkiln.drape.measure import fit_report

        report = fit_report(session.garment, session.drape.points, session.body)
        _heading(pdf, "Fit on body")
        _table(
            pdf,
            ["landmark", "body mm", "garment mm", "ease mm", "verdict"],
            [
                [
                    name,
                    f"{row['body_mm']:,.0f}",
                    f"{row['garment_mm']:,.0f}",
                    f"{row['ease_mm']:+,.0f}",
                    row["verdict"],
                ]
                for name, row in report["ease"].items()
            ],
            widths=[34, 26, 30, 26, 44],
        )
        _heading(pdf, "Strain by panel")
        _table(
            pdf,
            ["piece", "mean %", "p95 %", "compressed %"],
            [
                [
                    name,
                    f"{row['mean_pct']:.1f}",
                    f"{row['p95_pct']:.1f}",
                    f"{row['compressed_pct']:.1f}",
                ]
                for name, row in report["strain"]["panels"].items()
            ],
            widths=[44, 26, 26, 34],
        )
        sections += 2

    destination = Path(out)
    pdf.output(str(destination))
    return {
        "path": str(destination),
        "pages": pdf.pages_count if hasattr(pdf, "pages_count") else len(pdf.pages),
        "sections": sections,
        "pieces": len(session.pattern.panels),
        "fabric": cloth.name,
        "fabric_tier": str(cloth.tier),
        "includes_fit": session.drape is not None,
    }


def _heading(pdf, text: str) -> None:
    pdf.ln(3)
    pdf.set_font("helvetica", "B", HEAD_SIZE)
    pdf.set_fill_color(238, 238, 240)
    pdf.cell(0, 6, f" {text}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _table(pdf, header: list[str], rows: list[list[str]], *, widths: list[float]) -> None:
    pdf.set_font("helvetica", "B", BODY_SIZE)
    pdf.set_fill_color(250, 250, 250)
    for label, width in zip(header, widths, strict=False):
        pdf.cell(width, 5, label, border="B", fill=True)
    pdf.ln()
    pdf.set_font("helvetica", size=BODY_SIZE)
    for row in rows:
        for value, width in zip(row, widths, strict=False):
            pdf.cell(width, 5, str(value)[: int(width / 1.7)], border="B")
        pdf.ln()
