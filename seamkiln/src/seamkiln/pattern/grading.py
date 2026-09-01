"""Parametric grading: scale a pattern to a body from its measurements.

Two things are true at once and the module has to say both.

Industrial grading moves NAMED POINTS by per-size rules - a shoulder point
goes out 3 mm and up 1 mm per size, an armhole depth 6 mm - and those rules
are a pattern maker's craft, graded set by graded set. `GradeRule` in the
model carries exactly that, and `grade()` applies it.

What this module adds is the other half: **proportional grading from
measurements**, which is what "enter your basic body measurements and get a
pattern" means. It scales the block by the ratio of target to base
measurement, per axis and per region, and it is honest about being an
approximation: a proportional grade fits a body shaped like the block, and
the further the body is from that shape the more a real grade rule would
differ. The report says how far it stretched each axis so a pattern maker can
see whether to trust it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

import numpy as np

from seamkiln.pattern.geometry import Vertex
from seamkiln.pattern.model import Panel, Pattern

# How far a proportional grade may stretch before it stops being a grade and
# starts being a guess. Two sizes either side of a block is normal practice;
# beyond that a pattern maker re-drafts rather than grades.
SANE_RATIO = (0.80, 1.25)


@dataclass(slots=True)
class Measurements:
    """The numbers a tape measure gives, in millimetres."""

    chest: float = 1000.0
    waist: float = 860.0
    hip: float = 1020.0
    height: float = 1750.0
    shoulder: float = 460.0  # across-shoulder width
    back_length: float = 440.0  # nape to waist
    sleeve_length: float = 620.0
    neck: float = 380.0

    @classmethod
    def from_body(cls, mesh: Any) -> Measurements:
        """Measure a body mesh and grade to IT - the whole point of having a
        parametric body and a parametric pattern in the same tool."""
        from seamkiln.drape.garment import body_landmarks
        from seamkiln.drape.measure import body_measurements

        marks = body_landmarks(mesh)
        rows = body_measurements(mesh)["landmarks"]
        chest = marks["chest_girth_m"] * 1000.0
        waist_row = rows.get("waist", {})
        # Nape to waist, MEASURED between two landmark heights rather than
        # guessed as a fraction of the chest. The first version multiplied a
        # height difference by 2.6 and reported a 619 mm back on a 1.68 m
        # body, which is most of a torso.
        back = (
            (marks["shoulder_y_m"] - waist_row["y_m"]) * 1000.0
            if "y_m" in waist_row
            else marks["height_m"] * 250.0
        )
        return cls(
            chest=chest,
            waist=waist_row.get("girth_mm", chest * 0.86),
            hip=rows.get("hip", {}).get("girth_mm", chest * 1.02),
            height=marks["height_m"] * 1000.0,
            # across-shoulder is a WIDTH, not a girth: about 45% of the chest
            # girth on an adult block
            shoulder=chest * 0.45,
            back_length=back,
            # a neck cross-section on a crude mannequin is a poor tape
            # measure; take it if it is plausible, else scale off the chest
            neck=(
                marks["neck_girth_m"] * 1000.0
                if 0.28 * chest < marks.get("neck_girth_m", 0.0) * 1000.0 < 0.45 * chest
                else chest * 0.38
            ),
        )

    def as_dict(self) -> dict[str, float]:
        return asdict(self)

    def ratios(self, other: Measurements) -> dict[str, float]:
        return {
            f.name: (getattr(other, f.name) / getattr(self, f.name))
            if getattr(self, f.name)
            else 1.0
            for f in fields(self)
        }


class GradingError(ValueError):
    """A grade that would stretch the block past what a grade can honestly do."""


@dataclass(slots=True)
class GradeReport:
    base: dict[str, float]
    target: dict[str, float]
    ratios: dict[str, float]
    x_scale: float
    y_scale: float
    warnings: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ratios": {k: round(v, 4) for k, v in self.ratios.items()},
            "x_scale": round(self.x_scale, 4),
            "y_scale": round(self.y_scale, 4),
            "method": "proportional (girth on x, length on y)",
            "warnings": self.warnings,
            "note": "industrial grading moves named points by per-size rules; "
            "this scales the block. Use GradeRule for a true graded set.",
        }


def grade_to_measurements(
    pattern: Pattern,
    base: Measurements,
    target: Measurements,
    *,
    strict: bool = True,
) -> tuple[Pattern, GradeReport]:
    """Scale a pattern from one body's measurements to another's.

    Girth goes on the x axis (a panel's width is half a girth), length on y.
    Sleeves take the sleeve ratio rather than the body's, because an arm and
    a torso do not grade together.
    """
    ratios = base.ratios(target)
    warnings: list[str] = []
    for name, value in ratios.items():
        if not SANE_RATIO[0] <= value <= SANE_RATIO[1]:
            message = (
                f"{name} grades by x{value:.2f}, outside the sane band "
                f"{SANE_RATIO[0]}-{SANE_RATIO[1]}. A proportional grade this far "
                "from the block is a guess; re-draft instead."
            )
            if strict:
                raise GradingError(message)
            warnings.append(message)

    body_x = ratios["chest"]
    body_y = ratios["back_length"]
    sleeve_x = (ratios["chest"] + ratios["shoulder"]) / 2.0
    sleeve_y = ratios["sleeve_length"]

    graded: list[Panel] = []
    for panel in pattern.panels:
        sleeve = panel.id.upper().startswith("SLEEVE")
        sx, sy = (sleeve_x, sleeve_y) if sleeve else (body_x, body_y)
        graded.append(_scale_panel(panel, sx, sy))

    out = Pattern(
        name=f"{pattern.name} [graded]",
        panels=graded,
        seams=list(pattern.seams),
        grade_rules=dict(pattern.grade_rules),
        units=pattern.units,
        provenance={**pattern.provenance, "graded_from": base.as_dict()},
    )
    return out, GradeReport(
        base=base.as_dict(),
        target=target.as_dict(),
        ratios=ratios,
        x_scale=body_x,
        y_scale=body_y,
        warnings=warnings,
    )


def _scale_panel(panel: Panel, sx: float, sy: float) -> Panel:
    """Scale about the panel's own centre, so it grows outward rather than
    walking away from the origin."""
    points = np.asarray([(v.x, v.y) for v in panel.outline], dtype=np.float64)
    centre = points.mean(axis=0)

    def scale(x: float, y: float) -> tuple[float, float]:
        return (centre[0] + (x - centre[0]) * sx, centre[1] + (y - centre[1]) * sy)

    from seamkiln.pattern.model import InternalLine, Mark

    return Panel(
        id=panel.id,
        name=panel.name,
        outline=[Vertex(*scale(v.x, v.y), v.kind) for v in panel.outline],
        internals=[
            InternalLine(
                line.kind, [Vertex(*scale(v.x, v.y), v.kind) for v in line.points], line.closed
            )
            for line in panel.internals
        ],
        marks=[
            Mark(m.kind, *scale(m.x, m.y), depth=m.depth, diameter=m.diameter) for m in panel.marks
        ],
        seam_allowance_mm=panel.seam_allowance_mm,
        meta={**panel.meta, "graded": f"x{sx:.3f} y{sy:.3f}"},
    )


def size_run(
    pattern: Pattern, base: Measurements, *, steps: int = 3, chest_step_mm: float = 40.0
) -> dict[str, Pattern]:
    """A graded set either side of the block - what a factory asks for.

    40 mm of chest per size is the common step for adult outerwear; the other
    measurements move with it in the block's own proportions, which is what
    makes this a PROPORTIONAL run and not a drafted one.
    """
    run: dict[str, Pattern] = {}
    for step in range(-steps, steps + 1):
        if step == 0:
            run["base"] = pattern
            continue
        factor = 1.0 + (step * chest_step_mm) / base.chest
        target = Measurements(**{f.name: getattr(base, f.name) * factor for f in fields(base)})
        label = f"{'+' if step > 0 else ''}{step}"
        run[label], _ = grade_to_measurements(pattern, base, target, strict=False)
    return run
