"""Encoded drafting rules, with their provenance attached to each one.

PROVENANCE, stated plainly because it is load-bearing. The numeric rules here
come from TEE's own Knowledge Base entry `arch.drawing_documentation`
(`confidence: medium`, `jurisdiction: southern-africa`), which cites **SANS
10143 Building drawing practice** through public transcriptions plus a South
African public-tender drawing standard. They have NOT been checked against the
purchased SANS 10143 text, and CLAUDE.md's rule about the KB applies: it
grounds nothing on its own.

So every rule carries a `basis` naming where it came from, and a `firmness`:

  "sans10143"  the KB attributes this to SANS 10143 and the value is specific
  "convention" ordinary drafting practice the KB states without attribution
  "house"      this module's own choice, declared as such and not attributed

Nothing in here is presented as a quotation from a standard nobody has read.
Okongo Oneleiwa is in Namibia, where practice follows SANS-derived convention
and the City of Windhoek planning requirements the KB records for [NA].
"""

from __future__ import annotations

from dataclasses import dataclass, field

KB_ENTRY = "arch.drawing_documentation (TEE KB, confidence: medium)"
SANS = f"SANS 10143 Building drawing practice, via {KB_ENTRY}"
CONVENTION = f"drafting convention recorded in {KB_ENTRY}"

# -- sheets ----------------------------------------------------------------
# ISO A series. Landscape orientation is expressed as (width, height).
SHEET_SIZES_MM: dict[str, tuple[float, float]] = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
}

# -- text ------------------------------------------------------------------
# "titles 5 mm; grid references 3,5 mm; dimensions and general notes 2,5 mm"
TEXT_HEIGHTS_MM: tuple[float, ...] = (2.5, 3.5, 5.0, 7.0)
TEXT_MIN_MM = 2.5
TEXT_ROLE_MM = {"title": 5.0, "subtitle": 3.5, "grid": 3.5, "dimension": 2.5, "note": 2.5}
POINTS_PER_MM = 1 / 0.352777778  # 1 pt = 1/72 in

# -- lines -----------------------------------------------------------------
# "Line weight is the primary carrier of information in a drawing; a set with
#  one line weight is unreadable regardless of how much is drawn."
LINE_WEIGHTS_MM: tuple[float, ...] = (0.18, 0.25, 0.35, 0.50, 0.70, 1.00)
LINE_ROLE_MM = {
    "border": 0.70,  # "Very heavy 0,70-1,00 ... drawing border"
    "cut_primary": 0.70,  # section cut through primary structure/ground
    "cut_secondary": 0.50,  # building outline in plan
    "beyond": 0.35,  # elements in elevation beyond the cut
    "fitting": 0.25,  # fittings, sanitaryware, furniture
    "hatch": 0.18,  # hatching, grid lines, extension lines
}
MIN_DISTINCT_WEIGHTS = 3

# -- scales ----------------------------------------------------------------
# "Never invent a scale - 1:75 and 1:150 are unreadable with a standard rule."
PREFERRED_SCALES: tuple[int, ...] = (1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000)
SCALE_FOR_KIND = {
    "ga_plan": (100, 50),
    "ga_section": (100, 50),
    "ga_elevation": (100, 50),
    "enlarged_plan": (50, 20),
    "detail": (20, 10, 5),
    "site_plan": (500, 200),
    "pictorial": (),  # an axonometric carries no meaningful scale
}

# -- mandatory content -----------------------------------------------------
DO_NOT_SCALE = "DO NOT SCALE. WORK TO FIGURED DIMENSIONS."
TITLE_BLOCK_FIELDS: tuple[str, ...] = (
    "project",
    "client",
    "drawing_title",
    "drawing_number",
    "revision",
    "scale",
    "date",
    "drawn_by",
    "checked_by",
)
DIMENSION_CHAINS: tuple[str, ...] = ("overall", "grid", "opening")
LEVEL_PREFIXES = ("FFL", "SSL", "NGL", "SOFFIT")


@dataclass(frozen=True)
class Rule:
    code: str
    title: str
    basis: str
    firmness: str  # sans10143 | convention | house
    severity: str  # reject | correct | advise
    remedy: str = ""


RULES: tuple[Rule, ...] = (
    Rule(
        "SHEET-SIZE",
        "Sheet is a standard A-series size",
        CONVENTION,
        "convention",
        "reject",
        "Use A1/A2 to issue, A3 for the reduced set.",
    ),
    Rule(
        "BORDER-WEIGHT",
        "Drawing border is drawn very heavy (0,70-1,00 mm)",
        SANS,
        "sans10143",
        "correct",
        "Set the border to 0,70 mm.",
    ),
    Rule(
        "TEXT-MIN",
        "No plotted text below 2,5 mm",
        SANS,
        "sans10143",
        "correct",
        "Raise the text to the nearest height in the set.",
    ),
    Rule(
        "TEXT-SERIES",
        "Text heights come from the stated set",
        SANS,
        "sans10143",
        "correct",
        "Snap to 2,5 / 3,5 / 5 / 7 mm.",
    ),
    Rule(
        "LINE-HIERARCHY",
        "At least three distinct line weights are in use",
        SANS,
        "sans10143",
        "advise",
        "A set with one line weight is unreadable.",
    ),
    Rule(
        "LINE-SERIES",
        "Line weights come from the stated pen set",
        SANS,
        "sans10143",
        "correct",
        "Snap to 0,18 / 0,25 / 0,35 / 0,50 / 0,70 / 1,00 mm.",
    ),
    Rule(
        "SCALE-PREFERRED",
        "Scale is one of the preferred ratios",
        SANS,
        "sans10143",
        "reject",
        "Never invent a scale.",
    ),
    Rule(
        "SCALE-FOR-KIND",
        "Scale suits the drawing type",
        CONVENTION,
        "convention",
        "advise",
        "GA plans and sections are drawn at 1:100 or 1:50.",
    ),
    Rule(
        "DO-NOT-SCALE",
        "The do-not-scale note is present",
        SANS,
        "sans10143",
        "correct",
        f"Print '{DO_NOT_SCALE}' in the title block.",
    ),
    Rule(
        "NORTH-POINT",
        "Every plan carries a north point",
        SANS,
        "sans10143",
        "reject",
        "Required by SANS 10143 and by City of Windhoek [NA].",
    ),
    Rule(
        "TITLE-FIELDS",
        "The title block carries every mandatory field",
        CONVENTION,
        "convention",
        "correct",
        "Add the missing fields.",
    ),
    Rule(
        "REVISION",
        "A revision code, date, description and author are recorded",
        CONVENTION,
        "convention",
        "correct",
        "Issue as P01 with a revision table.",
    ),
    Rule(
        "DIM-CHAINS",
        "A GA plan carries overall, grid and opening dimension chains",
        SANS,
        "sans10143",
        "advise",
        "Never require the contractor to add or subtract to find a dimension.",
    ),
    Rule(
        "DIM-UNITS",
        "Building dimensions are millimetres without a unit suffix",
        SANS,
        "sans10143",
        "correct",
        "Strip the unit; state 'ALL DIMENSIONS IN MM'.",
    ),
    Rule(
        "LEVEL-DATUM",
        "Levels state the datum they are referenced to",
        SANS,
        "sans10143",
        "correct",
        "Name the benchmark or declare an assumed site datum.",
    ),
    Rule(
        "LEVEL-FORMAT",
        "Levels are written +0.000 to three decimals",
        SANS,
        "sans10143",
        "correct",
        "Use the +0.000 form.",
    ),
    Rule(
        "ROOM-ID",
        "Rooms carry a name AND a number",
        SANS,
        "sans10143",
        "correct",
        "The number is the key into the finishes schedule.",
    ),
    Rule(
        "MARKER-TARGET",
        "Every section or detail marker has a target sheet",
        SANS,
        "sans10143",
        "reject",
        "Audit for orphan markers before issue.",
    ),
    Rule(
        "SECTION-ON-PLAN",
        "Every section drawn has its cut line shown on a plan",
        SANS,
        "sans10143",
        "reject",
        "Draw the cut line with a direction of view.",
    ),
    Rule(
        "LEGIBILITY-OVERLAP",
        "No two pieces of text overlap on the plotted sheet",
        "house rule, declared as this module's own",
        "house",
        "correct",
        "A conforming sheet can still be unreadable; this tier measures the plot.",
    ),
    Rule(
        "LEGIBILITY-FRAME",
        "All content sits inside the drawing frame",
        CONVENTION,
        "convention",
        "reject",
        "Bring it inside the border.",
    ),
    Rule(
        "PROVENANCE",
        "A survey drawing states how it was measured and its accuracy",
        "house rule, declared as this module's own",
        "house",
        "advise",
        "An as-built drawing without a stated accuracy invites misuse.",
    ),
)

BY_CODE: dict[str, Rule] = {r.code: r for r in RULES}


def section_tag(view_name: str) -> str:
    """'SECTION A-A' -> 'A'. One definition, because the critic and the
    corrector disagreeing about what a tag is was a real bug: the critic
    looked for 'A-A', the corrector wrote 'A', and two REJECT findings
    survived a loop that reported itself converged."""
    # Hyphen, en-dash and em-dash all appear in real sheet titles; splitting
    # on only the ASCII one is how "SECTION B-B" and its en-dash twin ended up
    # as different tags.
    dashes = "-\u2010\u2011\u2012\u2013\u2014\u2015"
    last = view_name.split()[-1].strip(dashes)
    for dash in dashes:
        last = last.split(dash)[0]
    return last.upper()


def nearest(value: float, allowed: tuple[float, ...]) -> float:
    return min(allowed, key=lambda a: abs(a - value))


def snap_up(value: float, allowed: tuple[float, ...]) -> float:
    """Snap to the nearest allowed value at or above `value`."""
    above = [a for a in allowed if a >= value - 1e-9]
    return above[0] if above else allowed[-1]


@dataclass
class Finding:
    rule: str
    severity: str
    where: str
    detail: str
    remedy: str = ""
    autofixed: bool = False

    def line(self) -> str:
        mark = "FIXED " if self.autofixed else f"{self.severity.upper():6s}"
        return f"{mark} {self.rule:16s} {self.where:22s} {self.detail}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, code: str, where: str, detail: str, **kw) -> None:
        rule = BY_CODE[code]
        self.findings.append(
            Finding(
                code,
                kw.pop("severity", rule.severity),
                where,
                detail,
                kw.pop("remedy", rule.remedy),
                **kw,
            )
        )

    @property
    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "reject" and not f.autofixed]

    @property
    def open(self) -> list[Finding]:
        return [f for f in self.findings if not f.autofixed]

    def __len__(self) -> int:
        return len(self.findings)
