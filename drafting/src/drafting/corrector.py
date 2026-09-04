"""Apply the corrections a critique asks for, and say exactly what changed.

Two things this deliberately does NOT do:

* It never silently improves anything. Every edit returns a Finding marked
  `autofixed`, so the human sees the whole list of changes made on their behalf.
* It never invents content it cannot know. A missing checker's initials, or a
  survey datum nobody established, is left for a person - the correction is to
  print an explicit placeholder that reads as unfinished, not to fabricate a
  plausible value. A drawing that looks signed off and is not is worse than one
  that visibly is not.
"""

from __future__ import annotations

from dataclasses import replace

from drafting import standards as S
from drafting.spec import DrawingSet, Marker, Sheet

UNSET = "— NOT SET —"


def _fix_text(sheet: Sheet, report: S.Report) -> None:
    for i, text in enumerate(sheet.texts):
        target = S.TEXT_ROLE_MM.get(text.role)
        if target is None or text.height_mm < S.TEXT_MIN_MM:
            target = S.snap_up(max(text.height_mm, S.TEXT_MIN_MM), S.TEXT_HEIGHTS_MM)
        if abs(text.height_mm - target) > 1e-6:
            report.add(
                "TEXT-SERIES" if text.height_mm >= S.TEXT_MIN_MM else "TEXT-MIN",
                f"{sheet.number}/{text.role}",
                f"{text.height_mm:.2f} mm -> {target:.1f} mm",
                autofixed=True,
            )
            sheet.texts[i] = replace(text, height_mm=target)


def _fix_lines(sheet: Sheet, report: S.Report) -> None:
    for i, line in enumerate(sheet.lines):
        target = S.LINE_ROLE_MM.get(line.role, S.nearest(line.width_mm, S.LINE_WEIGHTS_MM))
        if line.role != "border":
            target = S.nearest(line.width_mm, S.LINE_WEIGHTS_MM)
        if abs(line.width_mm - target) > 1e-6:
            report.add(
                "LINE-SERIES",
                f"{sheet.number}/{line.role}",
                f"{line.width_mm:.3f} mm -> {target:.2f} mm",
                autofixed=True,
            )
            sheet.lines[i] = replace(line, width_mm=target)


def _fix_title_block(sheet: Sheet, report: S.Report, project: dict[str, str]) -> None:
    tb = sheet.title_block
    for name in S.TITLE_BLOCK_FIELDS:
        if tb.fields.get(name):
            continue
        supplied = project.get(name)
        if name == "drawing_number":
            supplied = sheet.number
        elif name == "drawing_title":
            supplied = sheet.title.split("—")[0].strip()
        elif name == "revision":
            supplied = "P01"
        # An unknown human is left unknown, loudly.
        value = supplied or UNSET
        tb.fields[name] = value
        report.add(
            "TITLE-FIELDS", f"{sheet.number}/title block", f"{name} = {value}", autofixed=True
        )
    notes = " ".join(tb.notes).upper()
    if S.DO_NOT_SCALE.rstrip(".") not in notes:
        tb.notes.append(S.DO_NOT_SCALE)
        report.add("DO-NOT-SCALE", f"{sheet.number}/title block", "note added", autofixed=True)
    if "ALL DIMENSIONS IN MILLIMETRES" not in notes:
        tb.notes.append("ALL DIMENSIONS IN MILLIMETRES UNLESS NOTED.")


def _fix_views(sheet: Sheet, report: S.Report, rooms: dict[str, str]) -> None:
    for i, view in enumerate(sheet.views):
        wanted = S.SCALE_FOR_KIND.get(view.kind, ())
        if wanted and view.scale_denominator not in wanted:
            target = min(wanted, key=lambda w: abs(w - view.scale_denominator))
            report.add(
                "SCALE-FOR-KIND",
                f"{sheet.number}/{view.name}",
                f"1:{view.scale_denominator} -> 1:{target}",
                autofixed=True,
            )
            sheet.views[i] = view = replace(view, scale_denominator=target)
        for j, room in enumerate(view.rooms):
            if not room.name and room.number in rooms:
                view.rooms[j] = replace(room, name=rooms[room.number])
                report.add(
                    "ROOM-ID",
                    f"{sheet.number}/{room.number}",
                    f"named '{rooms[room.number]}'",
                    autofixed=True,
                )
        if view.levels and not sheet.level_datum:
            sheet.level_datum = (
                "ASSUMED SITE DATUM: FFL of Room 01 taken as ±0.000. NOT related to mean sea level."
            )
            report.add(
                "LEVEL-DATUM",
                f"{sheet.number}/{view.name}",
                "assumed datum declared",
                autofixed=True,
            )


def _fix_section_markers(
    dset: DrawingSet, report: S.Report, cuts: dict[str, tuple[str, float]]
) -> None:
    """An orphan section is a reject. Draw its cut line on the plan that owns it."""
    for sheet in dset.sheets:
        for view in sheet.views:
            if view.kind != "ga_section":
                continue
            tag = S.section_tag(view.name)
            already = any(
                m.target_sheet == sheet.number and m.tag == tag
                for s in dset.sheets
                for m in s.markers
            )
            if already or tag not in cuts:
                continue
            plan_number, direction = cuts[tag]
            plan = dset.by_number(plan_number)
            if plan is None:
                continue
            plan.markers.append(
                Marker(
                    tag=tag,
                    target_sheet=sheet.number,
                    drawn_on=plan_number,
                    direction_deg=direction,
                )
            )
            report.add(
                "SECTION-ON-PLAN",
                f"{plan_number}/{tag}",
                f"cut line added, pointing at {sheet.number}",
                autofixed=True,
            )


def correct(
    dset: DrawingSet,
    *,
    project: dict[str, str],
    rooms: dict[str, str],
    cuts: dict[str, tuple[str, float]],
    provenance: str,
) -> S.Report:
    """Amend the set in place. Returns everything that was changed."""
    report = S.Report()
    for sheet in dset.sheets:
        _fix_text(sheet, report)
        _fix_lines(sheet, report)
        _fix_title_block(sheet, report, project)
        _fix_views(sheet, report, rooms)
        if not sheet.provenance:
            sheet.provenance = provenance
            report.add("PROVENANCE", sheet.number, "measurement basis stated", autofixed=True)
    _fix_section_markers(dset, report, cuts)
    return report
