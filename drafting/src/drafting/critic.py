"""The critic: read a drawing set, report where it departs from the rules.

It reports, it does not redraw. Corrections are a separate, explicit step, so
that a fault and its fix are never confused with each other and so a human can
see everything that was changed on their behalf.
"""

from __future__ import annotations

from drafting import standards as S
from drafting.spec import DrawingSet, Sheet


def critique_sheet(sheet: Sheet, whole_set: DrawingSet | None = None) -> S.Report:
    report = S.Report()
    W = sheet.number

    if sheet.size not in S.SHEET_SIZES_MM:
        report.add("SHEET-SIZE", W, f"'{sheet.size}' is not an A-series size")

    # -- text ---------------------------------------------------------------
    for text in sheet.texts:
        label = f"{W}/{text.role}"
        if text.height_mm < S.TEXT_MIN_MM - 1e-9:
            report.add(
                "TEXT-MIN", label, f"{text.height_mm:.2f} mm plotted, minimum is {S.TEXT_MIN_MM} mm"
            )
        elif not any(abs(text.height_mm - h) < 1e-6 for h in S.TEXT_HEIGHTS_MM):
            report.add(
                "TEXT-SERIES", label, f"{text.height_mm:.2f} mm is not in {S.TEXT_HEIGHTS_MM}"
            )

    # -- lines --------------------------------------------------------------
    widths = {round(line.width_mm, 3) for line in sheet.lines}
    if sheet.lines and len(widths) < S.MIN_DISTINCT_WEIGHTS:
        report.add(
            "LINE-HIERARCHY", W, f"only {len(widths)} distinct line weight(s): {sorted(widths)}"
        )
    for line in sheet.lines:
        if not any(abs(line.width_mm - w) < 1e-6 for w in S.LINE_WEIGHTS_MM):
            report.add(
                "LINE-SERIES",
                f"{W}/{line.role}",
                f"{line.width_mm:.3f} mm is not a standard pen width",
            )
        if line.role == "border" and line.width_mm < 0.70 - 1e-9:
            report.add(
                "BORDER-WEIGHT",
                f"{W}/border",
                f"{line.width_mm:.3f} mm; the border is a very-heavy line",
            )

    # -- views --------------------------------------------------------------
    for view in sheet.views:
        label = f"{W}/{view.name}"
        if view.kind != "pictorial":
            if view.scale_denominator not in S.PREFERRED_SCALES:
                report.add(
                    "SCALE-PREFERRED", label, f"1:{view.scale_denominator} is not a preferred ratio"
                )
            wanted = S.SCALE_FOR_KIND.get(view.kind, ())
            if wanted and view.scale_denominator not in wanted:
                report.add(
                    "SCALE-FOR-KIND",
                    label,
                    f"1:{view.scale_denominator} for a {view.kind}; "
                    f"expected {' or '.join(f'1:{w}' for w in wanted)}",
                )
        if view.kind == "ga_plan":
            if not view.north_point:
                report.add("NORTH-POINT", label, "no north point on a plan")
            missing = [c for c in S.DIMENSION_CHAINS if c not in view.dimension_chains]
            if missing:
                report.add("DIM-CHAINS", label, f"missing the {', '.join(missing)} chain(s)")
            for room in view.rooms:
                if not room.name:
                    report.add("ROOM-ID", f"{label}/{room.number}", "room has a number but no name")
        for level in view.levels:
            if not any(level.startswith(p) for p in S.LEVEL_PREFIXES):
                report.add("LEVEL-FORMAT", label, f"'{level}' has no level prefix")
            elif "±" not in level and "+" not in level and "-" not in level:
                report.add("LEVEL-FORMAT", label, f"'{level}' carries no signed value")
        if view.levels and not sheet.level_datum:
            report.add("LEVEL-DATUM", label, "levels shown but no datum stated")

    # -- title block --------------------------------------------------------
    missing = [f for f in S.TITLE_BLOCK_FIELDS if not sheet.title_block.fields.get(f)]
    if missing:
        report.add("TITLE-FIELDS", f"{W}/title block", f"missing {', '.join(missing)}")
    if not sheet.title_block.fields.get("revision"):
        report.add("REVISION", f"{W}/title block", "no revision code")
    notes = " ".join(sheet.title_block.notes).upper()
    if S.DO_NOT_SCALE.rstrip(".") not in notes:
        report.add("DO-NOT-SCALE", f"{W}/title block", "the do-not-scale note is absent")
    if sheet.dimension_units != "mm":
        report.add("DIM-UNITS", W, f"dimensions given in {sheet.dimension_units}")
    if not sheet.provenance:
        report.add("PROVENANCE", W, "no statement of how this was measured")

    # -- across the set -----------------------------------------------------
    if whole_set is not None:
        for marker in sheet.markers:
            if whole_set.by_number(marker.target_sheet) is None:
                report.add(
                    "MARKER-TARGET",
                    f"{W}/{marker.tag}",
                    f"points at {marker.target_sheet}, which is not in the set",
                )
        for view in sheet.views:
            if view.kind != "ga_section":
                continue
            tag = S.section_tag(view.name)
            drawn = [
                m
                for s in whole_set.sheets
                for m in s.markers
                if m.target_sheet == sheet.number and m.tag == tag
            ]
            if not drawn:
                report.add(
                    "SECTION-ON-PLAN",
                    f"{W}/{view.name}",
                    f"section {tag} is drawn but no plan shows its cut line",
                )
    return report


def critique(drawing_set: DrawingSet) -> S.Report:
    report = S.Report()
    for sheet in drawing_set.sheets:
        report.findings.extend(critique_sheet(sheet, drawing_set).findings)
    return report
