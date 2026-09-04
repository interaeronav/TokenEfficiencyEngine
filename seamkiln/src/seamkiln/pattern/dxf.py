"""DXF pattern interchange: the AAMA and ASTM dialects, on ezdxf (MIT).

ASTM D6673 - "Standard Practice for Sewn Products Pattern Data Interchange"
- **was withdrawn in 2019** and is still what the industry exchanges. It is
based on AutoCAD DXF R13, stores one style per file, uses **one BLOCK per
pattern piece**, and assigns features to 23 predefined layers. AAMA
published its own mapping first; the two are close cousins that number some
layers differently, so this module keeps the mapping as DATA (`Dialect`)
rather than as code, and every entry carries where it came from.

The writer exists to be read by somebody else's software, so every choice
below is settled by what the receiving systems and two real CLO 2024
exports actually do, measured on 2026-09-04 with ezdxf 1.4.4:

  1. **We write R12, and export it through
     `ezdxf.addons.gerber_D6673`.** ezdxf cannot write R13 (`Unsupported
     DXF version "AC1012"`), and R13 is not what the far end wants anyway:
     Gerber Technology's parser takes **R12 only**, with no
     `*Model_Space`/`*Paper_Space` block definitions, an empty HEADER and
     no TABLES section. That add-on ships in ezdxf precisely to write that
     file. Measured on our own output: no `*Model_Space`, no
     `*Paper_Space`, no TABLES, and it re-reads as AC1009. An earlier
     version of this module wrote R2000 and said here that the layout
     blocks could not be removed - that was wrong, and the file it made
     could not be opened by the one system this format exists for.
  2. **The unit rides in the Style System Text, not in `$INSUNITS`.** R12
     exports no `$INSUNITS` (ezdxf warns), and neither of the two real CLO
     files sets that key at all: both declare `UNITS: METRIC` as SST, which
     is **centimetres**. So the writer emits centimetres, `_resolve_units`
     reads them back through the same rung, and R2000 - kept only for a
     generic CAD viewer - sets `$INSUNITS 5` so its two declarations agree
     instead of contradicting each other.
  3. **The boundary is a heavy `POLYLINE`.** ezdxf refuses `LWPOLYLINE`
     below R2000, and heavy POLYLINE is what CLO, Gerber and Lectra write;
     the reader takes both.
  4. **D6673 is 7-bit ASCII, and the R12 export enforces it.** A character
     outside ASCII is written as an `\\xNN` escape and does *not* decode on
     the way back, so `write_dxf` names every string that had to be escaped
     in `non_ascii_escaped` rather than losing an accent quietly.

Reading is a different problem, because the file was written by somebody
else and **a unit declaration is a claim, not a measurement**. Three real
writers now tell three different unit stories: CLO omits `$INSUNITS` and is
saved by its header text, Seamly2D omits it and is saved by the millimetre
fallback, and **Optitex sets it and sets it wrong** - a purchased AAMA block
measured 2026-09-04 declares `$INSUNITS 6` (metres) and draws in inches, so
believing it made a 930 mm dress front 36,622 mm, a factor of **39.37**,
with every seam closed and every fit number confident. That is the exact
silent failure this module exists to prevent, so `$INSUNITS` is no longer
the highest rung the reader can reach. The ladder `_resolve_units` climbs:

    1. an explicit `units_mm=` argument
    2. **a control piece, MEASURED** - the only rung checkable against the
       drawing itself, and the one that caught Optitex
    3. a non-zero `$INSUNITS`
    4. the header's `UNITS:` system text
    5. millimetres, with a note

When rung 2 and a lower rung disagree the measured square wins, loudly:
`ReadReport.units_conflict` names both numbers and the ratio, and a note
says so. The read is not refused - we are not uncertain - and it is not
passed over either, because a file whose own control square contradicts its
header is broken and its owner has to be told.

Vertex tags round-trip through the standard itself: layers 2 and 3 hold the
turn points and curve points as POINT entities, so a corner comes back a
corner instead of being re-guessed from angles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.addons import gerber_D6673
from shapely.geometry import LinearRing, Point

from seamkiln.pattern.geometry import Polyline, Vertex, VertexKind, area
from seamkiln.pattern.model import InternalLine, LineKind, Mark, MarkKind, Panel, Pattern

# $INSUNITS -> millimetres per drawing unit. 0 is "unitless", which is not a
# unit but a missing declaration. A NON-zero value is only the THIRD rung of
# the ladder: a measured control piece outranks it, because Optitex ships
# files whose $INSUNITS is 39.37x wrong (see the module docstring). Below it
# come the header text and then millimetres with a note - `_resolve_units`.
INSUNITS_TO_MM: dict[int, float] = {0: 1.0, 1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0}
POINT_TOLERANCE_MM = 1e-6

# The one geometric convention of the written file: `UNITS: METRIC` is
# centimetres (see `HEADER_UNITS_TO_MM`), so a millimetre model is divided by
# ten on the way out and multiplied by ten on the way back. Measured over the
# 3,312 coordinates of the tee block and both real CLO files, x/10*10 differs
# from x by at most 1.1e-13 mm - eight orders below the 1e-6 mm the round-trip
# and the session fingerprint round to.
DRAWING_UNIT_MM = 10.0
SST_UNITS = "METRIC"
CM_INSUNITS = 5
SST_TEXT_HEIGHT = 0.25  # drawing units, the height both CLO exports write

# R12 is the interoperable one and therefore the default. R2000 is kept for a
# generic CAD viewer that wants a real header and layer table; Gerber's parser
# refuses it, so `write_dxf` reports `gerber_safe: False` when it is asked for.
DXF_VERSIONS = ("R12", "R2000")


@dataclass(frozen=True)
class Dialect:
    """A feature -> DXF layer map, with its provenance attached.

    `verified` is not decoration. The ASTM table was read off a published
    description of the standard; the AAMA table was assembled from secondary
    sources naming its layers. Writing a feature this dialect has no layer
    for is refused by name rather than guessed into a neighbouring layer.
    """

    name: str
    layers: dict[str, int]
    source: str
    verified: bool = False
    notes: str = ""

    def layer_for(self, feature: str) -> str:
        if feature not in self.layers:
            raise DxfDialectError(
                f"dialect {self.name!r} has no layer for {feature!r} "
                f"(it defines: {', '.join(sorted(self.layers))}). "
                f"{self.notes or 'Use a dialect that carries this feature.'}"
            )
        return str(self.layers[feature])

    def feature_for(self, layer: str) -> str | None:
        for feature, number in self.layers.items():
            if str(number) == str(layer).strip():
                return feature
        return None


class DxfDialectError(ValueError):
    """A feature or layer the chosen dialect does not define."""


# Verified against the published description of ASTM D6673-10's 23 layers
# (docs/research/67 section 4). Layer 0 is deliberately unused by the standard.
#
# `verified` here means the TABLE was read off that description - it does NOT
# mean a real file was ever seen using every row. Measured 2026-09-04: the two
# CLO 2024 exports exercise 8 of these 18 layers (1, 2, 3, 4, 7, 8, 84, 85) and
# Seamly2D's AAMA export writes 2 (1, 8); no free Gerber, Lectra or Optitex
# file could be found, and every substitute writes FEWER layers, not more. The
# other ten are unwitnessed, which is why a read reports `observed_layers`:
# field evidence has to accumulate before anyone may claim it.
ASTM = Dialect(
    name="astm",
    source="ASTM D6673-10 (withdrawn 2019); table in docs/research/67 §4",
    verified=True,
    layers={
        "boundary": 1,
        "turn_point": 2,
        "curve_point": 3,
        "notch": 4,
        "grade_reference": 5,
        "mirror": 6,
        "grain": 7,
        "internal": 8,
        "stripe": 9,
        "plaid": 10,
        "cutout": 11,
        "drill": 13,
        "sew": 14,
        "check_notch": 82,
        "qv_boundary": 84,
        "qv_internal": 85,
        "qv_cutout": 86,
        "qv_sew": 87,
    },
)

# AAMA shares the low-numbered layers with ASTM and adds its own; it has no
# published internal-cutout or quality-validation layers, so writing those to
# an AAMA file is refused rather than mapped somewhere plausible.
AAMA = Dialect(
    name="aama",
    source="AAMA layer names as reported by secondary sources, 2026-09-01",
    verified=False,
    notes=(
        "AAMA defines no internal-cutout (11), check-notch (82) or "
        "quality-validation (84-87) layers; export ASTM if the piece uses them."
    ),
    layers={
        "boundary": 1,
        "turn_point": 2,
        "curve_point": 3,
        "notch": 4,
        "grade_reference": 5,
        "mirror": 6,
        "grain": 7,
        "internal": 8,
        "drill": 13,
        "sew": 14,
        "drill_second": 15,
        "text": 19,
    },
)

DIALECTS: dict[str, Dialect] = {"astm": ASTM, "aama": AAMA}

_LINE_FEATURE: dict[LineKind, str] = {
    LineKind.INTERNAL: "internal",
    LineKind.CUTOUT: "cutout",
    LineKind.SEW: "sew",
    LineKind.GRAIN: "grain",
    LineKind.MIRROR: "mirror",
    LineKind.DART: "internal",
    LineKind.PLEAT: "internal",
    LineKind.STRIPE: "stripe",
    LineKind.PLAID: "plaid",
}
_MARK_FEATURE: dict[MarkKind, str] = {
    MarkKind.NOTCH_SLIT: "notch",
    MarkKind.NOTCH_V: "notch",
    MarkKind.NOTCH_CHECK: "check_notch",
    MarkKind.DRILL: "drill",
}


def dialect(name: str) -> Dialect:
    key = str(name or "").strip().lower()
    if key not in DIALECTS:
        raise DxfDialectError(
            f"unknown DXF dialect {name!r}; seamkiln writes: {', '.join(sorted(DIALECTS))}"
        )
    return DIALECTS[key]


# -- writing -----------------------------------------------------------------


def write_dxf(
    pattern: Pattern,
    path: str | Path,
    *,
    flavour: str = "astm",
    version: str = "R12",
) -> dict[str, Any]:
    """Write one style to one file: a block per piece, features on layers.

    `version` defaults to **R12** because the whole point of this format is
    that somebody else's software reads it, and R12 through
    `ezdxf.addons.gerber_D6673` is the only shape Gerber's parser accepts:
    no layout blocks, no TABLES, an empty HEADER, 7-bit ASCII. "R2000" is
    the opt-out for a generic CAD viewer that wants a header and a layer
    table - the report marks it `gerber_safe: False`, and it carries the
    same centimetre geometry so the two versions never disagree about size.
    """
    spec = dialect(flavour)
    release = str(version or "").strip().upper()
    if release not in DXF_VERSIONS:
        raise DxfDialectError(
            f"unknown DXF version {version!r}; seamkiln writes: {', '.join(DXF_VERSIONS)}. "
            f"R12 is the default because it is the only one pattern CAD and cutters read."
        )
    doc = ezdxf.new(dxfversion=release, setup=False)
    if release != "R12":
        # R12 exports no $INSUNITS at all, so the unit travels as SST for both
        # versions; 5 is centimetres, which is what the SST declares.
        doc.header["$INSUNITS"] = CM_INSUNITS
    for number in sorted(spec.layers.values()):
        doc.layers.add(str(number))

    modelspace = doc.modelspace()
    written: dict[str, int] = {}
    escaped: list[str] = []
    boundary_layer = spec.layer_for("boundary")

    # The Style System Text is mandatory and belongs on layer 1 with the
    # boundary (D6673; research doc 67 section 4). It goes down first, the way
    # a header should read.
    for line in _style_system_text(pattern):
        _add_text(modelspace, line, (0.0, 0.0), boundary_layer, escaped)

    for panel in pattern.panels:
        block = doc.blocks.new(_block_name(panel.id))
        # ASTM layer 1 is the PIECE BOUNDARY, which is the cut line. seamkiln
        # holds the sew line as the outline, so the allowance is applied here
        # - and the sew line goes to layer 14, where the standard puts it.
        from seamkiln.pattern.allowance import cut_line

        boundary = cut_line(panel) if panel.seam_allowance_mm else panel.outline
        _add_polyline(block, boundary, boundary_layer, closed=True)
        written["boundary"] = written.get("boundary", 0) + 1
        if panel.seam_allowance_mm:
            _add_polyline(block, panel.outline, spec.layer_for("sew"), closed=True)
            written["sew"] = written.get("sew", 0) + 1

        for vertex in boundary:
            feature = "turn_point" if vertex.kind is VertexKind.TURN else "curve_point"
            block.add_point(
                _units(vertex.x, vertex.y), dxfattribs={"layer": spec.layer_for(feature)}
            )
            written[feature] = written.get(feature, 0) + 1

        for internal in panel.internals:
            feature = _LINE_FEATURE[internal.kind]
            _add_polyline(block, internal.points, spec.layer_for(feature), closed=internal.closed)
            written[feature] = written.get(feature, 0) + 1

        for mark in panel.marks:
            feature = _MARK_FEATURE[mark.kind]
            block.add_point(_units(mark.x, mark.y), dxfattribs={"layer": spec.layer_for(feature)})
            written[feature] = written.get(feature, 0) + 1

        # Piece System Text: the standard's way of naming a piece, inside its
        # block, in the same "KEY: value" shape the reader parses back.
        _add_text(
            block,
            f"Piece Name: {panel.name}",
            _units(panel.bbox[0], panel.bbox[1]),
            boundary_layer,
            escaped,
        )
        modelspace.add_blockref(block.name, (0.0, 0.0))

    destination = Path(path)
    if release == "R12":
        # This is the fix: the add-on writes the BLOCKS section without the
        # *Model_Space / *Paper_Space definitions, an empty HEADER and no
        # TABLES section, in 7-bit ASCII.
        gerber_D6673.export_file(doc, destination)
    else:
        doc.saveas(destination)
    return {
        "path": str(destination),
        "dialect": spec.name,
        "dialect_verified": spec.verified,
        "dxfversion": release,
        "dxfversion_note": (
            "ASTM D6673 is based on R13, which ezdxf cannot write; R12 is what "
            "Gerber's parser accepts, and the export strips the layout blocks, "
            "the TABLES section and the header"
            if release == "R12"
            else "R2000 keeps a header and a layer table; Gerber's parser refuses it"
        ),
        "gerber_safe": release == "R12",
        "sst_units": SST_UNITS,
        "drawing_unit_mm": DRAWING_UNIT_MM,
        "pieces": len(pattern.panels),
        "entities": written,
        "layout_blocks_present": [] if release == "R12" else ["*Model_Space", "*Paper_Space"],
        "non_ascii_escaped": escaped,
    }


def _style_system_text(pattern: Pattern) -> list[str]:
    """The mandatory Style System Text, in the shape real files carry.

    Measured verbatim off two CLO 2024 DXF-AAMA/ASTM exports (2026-09-04):
    eight `KEY: value` lines on layer 1, in this order, `VERSION: 3` in both.
    The standard requires a case-sensitive syntax "in a mix of upper and
    lower case characters" (ezdxf discussion #789 quoting D6673) whose exact
    spelling lives in the paywalled text. Two real vendors write the SAME
    KEYS in different case, measured 2026-09-04: CLO 2024 is ALL CAPS
    ("PIECE NAME", "UNITS", "AUTHOR"), the purchased Optitex AAMA block is
    Title Case ("Piece Name", "Units: ENGLISH", "Author: Optitex").

    We write TITLE CASE, Optitex's, because it is the form the standard
    describes and the form that discussion says the all-caps sample
    VIOLATED - so on this point CLO is the non-conforming writer and
    following it would propagate its mistake. The cost is nil: the reader
    upper-cases every key before matching, so it takes either, and the
    round trip is unaffected. Write to the standard, read what arrives.

    `SAMPLE SIZE` is a fact about the style, not about the writer: it is
    carried over from a file we read and left out when nobody has said it.
    """
    inherited = {
        str(key).upper(): str(value)
        for key, value in (pattern.provenance.get("header") or {}).items()
    }
    stamped = datetime.now()
    fields = (
        ("Style Name", pattern.name),
        ("Creation Date", stamped.strftime("%d-%m-%Y")),
        ("Creation Time", stamped.strftime("%H:%M")),
        ("Author", "seamkiln"),
        ("Product", f"seamkiln {_product_version()}"),
        ("Version", "3"),  # the SST format version both measured exports carry
        ("Sample Size", inherited.get("SAMPLE SIZE", "")),
        ("Units", SST_UNITS),
    )
    return [f"{key}: {value}" for key, value in fields if value]


def _product_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("seamkiln")
    except PackageNotFoundError:  # run straight off src/, never installed
        return "dev"


def _block_name(piece_id: str) -> str:
    """A block name D6673 can carry: 7-bit ASCII, no spaces.

    The export is ASCII-only, and a non-ASCII block name comes back as its
    escape rather than as itself (ezdxf rejects the reloaded name outright),
    so an accent is folded to `_` here, where it is visible, instead of
    breaking the re-read.
    """
    safe = "".join(ch if (ch.isascii() and ch.isalnum()) or ch in "_-" else "_" for ch in piece_id)
    return safe or "PIECE"


def _units(x_mm: float, y_mm: float) -> tuple[float, float]:
    """Millimetres -> the file's drawing unit (centimetres; see the header)."""
    return (x_mm / DRAWING_UNIT_MM, y_mm / DRAWING_UNIT_MM)


def _add_polyline(block, points: Polyline, layer: str, *, closed: bool) -> None:
    """A heavy `POLYLINE`, not an `LWPOLYLINE`.

    ezdxf refuses LWPOLYLINE below R2000 (`LWPOLYLINE requires DXF R2000`),
    and the heavy POLYLINE is what CLO, Gerber and Lectra write anyway, so
    both versions use it and the reader keeps taking either.
    """
    block.add_polyline2d(
        [_units(v.x, v.y) for v in points], close=closed, dxfattribs={"layer": layer}
    )


def _add_text(space, text: str, at: tuple[float, float], layer: str, escaped: list[str]) -> None:
    """One system-text line, remembering anything ASCII-7 cannot carry.

    D6673 is 7-bit ASCII and the R12 export enforces it: a character outside
    it is written as `\\xNN` and does NOT decode on re-read, so the string is
    recorded and reported instead of being lost between two silent layers.
    """
    if not text.isascii():
        escaped.append(text)
    space.add_text(text, height=SST_TEXT_HEIGHT, dxfattribs={"layer": layer}).set_placement(at)


# -- reading -----------------------------------------------------------------

# The style/piece "system text" of AAMA and ASTM files: TEXT entities of the
# form "KEY: value" in model space (the style) and inside each block (the
# piece). CLO writes STYLE NAME / AUTHOR / PRODUCT / UNITS / SAMPLE SIZE at
# the top and PIECE NAME / SIZE / QUANTITY / "# n" per piece.
_SYSTEM_TEXT = re.compile(r"^\s*([A-Za-z][A-Za-z /_-]*?)\s*:\s*(.*?)\s*$")

# Header "UNITS:" -> millimetres per drawing unit. The standard's METRIC is
# centimetres, not millimetres: measured on two CLO 2024 exports (a women's
# tee front reads 45.5 x 61.0 cm, a trouser leg 38.4 x 104.2), and it is the
# Gerber/Lectra convention the header keyword comes from. ENGLISH is inches.
HEADER_UNITS_TO_MM: dict[str, float] = {
    "METRIC": 10.0,
    "CENTIMETERS": 10.0,
    "CENTIMETRES": 10.0,
    "CM": 10.0,
    "MILLIMETERS": 1.0,
    "MILLIMETRES": 1.0,
    "MM": 1.0,
    "ENGLISH": 25.4,
    "INCHES": 25.4,
    "INCH": 25.4,
    "IN": 25.4,
}

# a piece whose longest side is outside this band is almost certainly read
# in the wrong unit; the reader says so instead of handing back a 6 m sleeve
PLAUSIBLE_PIECE_MM = (20.0, 3000.0)

# A CONTROL PIECE is ground truth by construction: a square of stated size,
# marked DO NOT CUT, is in a pattern file for exactly one reason - so the
# receiving system can check its own scale against something it can measure.
# `DO NOT CUT` is an instruction from the file's author and is always obeyed;
# `CONTROL` in a piece name is only a candidate, believed once it verifies.
CONTROL_NO_CUT = "DO NOT CUT"
CONTROL_NAME = "CONTROL"
# the drawn shape must match the shape its label claims this closely before
# the label is trusted; a control square that is not square is not evidence
CONTROL_ASPECT_TOLERANCE = 0.02

# "10\"X10\"", "25 cm x 25 cm", "250mm X 250mm". A size with NO unit token is
# ambiguous by construction and is never guessed at - inches and centimetres
# are a factor of 2.54 apart and the whole point of the piece is to be sure.
_CONTROL_UNITS_MM: dict[str, float] = {
    '"': 25.4,
    "IN": 25.4,
    "INCH": 25.4,
    "INCHES": 25.4,
    "\u201d": 25.4,
    "\u2033": 25.4,
    "CM": 10.0,
    "MM": 1.0,
}
_CONTROL_UNIT = r'(?:"|\u201d|\u2033|(?:inches|inch|in|cm|mm)(?![A-Za-z]))'
_CONTROL_LABEL = re.compile(
    r"(?P<w>\d+(?:\.\d+)?)\s*(?P<wu>" + _CONTROL_UNIT + r")?"
    r"\s*[x\u00d7]\s*"
    r"(?P<h>\d+(?:\.\d+)?)\s*(?P<hu>" + _CONTROL_UNIT + r")?",
    re.IGNORECASE,
)
_QV_FEATURES = ("qv_boundary", "qv_internal", "qv_cutout", "qv_sew")


@dataclass
class ReadReport:
    """What one read found, including what it could NOT name.

    `unknown_layers` is a census, not a tally: layer -> what is on it. Ten of
    the eighteen ASTM layers this module defines have never been seen in a
    real export (see the `ASTM` table), and no free Gerber/Lectra/Optitex
    file exists to close that gap, so the first real file anyone opens is
    the only teacher available. "layer 13 holds 24 POINT entities across 11
    pieces" tells a pattern maker it is the drill holes; "layer 13: 24" does
    not. `observed_layers` is the other half of the same evidence - which of
    the layers the dialect DOES define this file actually exercised, which
    is what a future claim of field verification would have to rest on. A
    defined-but-never-seen layer is not an unknown one; the two never mix.
    """

    pieces: int = 0
    unknown_layers: dict[str, dict[str, Any]] = field(default_factory=dict)
    observed_layers: list[str] = field(default_factory=list)
    skipped_blocks: list[str] = field(default_factory=list)
    scale_mm: float = 1.0
    insunits: int = 0
    units_source: str = ""
    header: dict[str, str] = field(default_factory=dict)
    validation_curves: int = 0
    qv_deviation_mm: float = 0.0
    control_piece: dict[str, Any] | None = None
    units_conflict: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ControlPiece:
    """A scale square a pattern file carries so a reader can check itself.

    Industry practice, and ground truth by construction: a square of stated
    size marked DO NOT CUT is in the file for exactly one reason. It outranks
    `$INSUNITS` because it is measurable and a header field is only a claim -
    an Optitex AAMA file measured 2026-09-04 declares `$INSUNITS 6` (metres)
    and draws in inches, a factor of 39.37 that every downstream number would
    have swallowed in silence.

    `mm_per_unit` is None when the piece could not be verified, and `problem`
    then says why in one line. A size with no unit token is never guessed at.
    """

    block: str
    label: str
    raw: tuple[float, float]
    size_mm: tuple[float, float] | None = None
    mm_per_unit: float | None = None
    never_cut: bool = False
    # it named itself CONTROL, or its label is shaped like a size: either way
    # it advertised a scale reference, so a failure to use it must be said
    advertised: bool = False
    problem: str = ""

    def summary(self) -> dict[str, Any]:
        """JSON-safe scalars only: this rides in a report a model may read."""
        out: dict[str, Any] = {
            "block": self.block,
            "label": self.label,
            "drawn": [round(v, 6) for v in self.raw],
        }
        if self.size_mm is not None:
            out["size_mm"] = [round(v, 3) for v in self.size_mm]
        if self.mm_per_unit is not None:
            out["mm_per_unit"] = self.mm_per_unit
        if self.problem:
            out["problem"] = self.problem
        return out


def _parse_control_label(label: str) -> tuple[float, float] | None:
    """ "10\"X10\"" -> (254.0, 254.0). None when it cannot be read WITHOUT guessing.

    A size with no unit token, or with two that disagree, is ambiguous by
    construction - inches and centimetres are a factor of 2.54 apart, and the
    entire purpose of this piece is to be certain. Ambiguity falls through to
    the next rung with a note; it never picks a unit on the balance of odds.
    """
    match = _CONTROL_LABEL.search(label or "")
    if match is None:
        return None
    tokens = {
        _CONTROL_UNITS_MM[token.upper()]
        for token in (match.group("wu"), match.group("hu"))
        if token
    }
    if len(tokens) != 1:  # none stated, or two that contradict each other
        return None
    per_unit = tokens.pop()
    return float(match.group("w")) * per_unit, float(match.group("h")) * per_unit


def _raw_extent(block, layer: str) -> tuple[float, float] | None:
    """The block's boundary extent in DRAWING UNITS - before any scale, since
    finding the scale is the whole point."""
    xs: list[float] = []
    ys: list[float] = []
    for entity in block:
        if entity.dxf.layer != layer or entity.dxftype() not in ("LWPOLYLINE", "POLYLINE"):
            continue
        points, _ = _polyline_points(entity, 1.0)
        xs += [v.x for v in points]
        ys += [v.y for v in points]
    if not xs:
        return None
    return max(xs) - min(xs), max(ys) - min(ys)


def _measure_control(
    block, spec: Dialect, record: dict[str, str], *, advertised: bool
) -> ControlPiece:
    """Verify a candidate before believing it. A false positive here rescales
    a whole garment, so the drawn shape must match the shape the label claims
    before the label is allowed to set the unit."""
    label = record.get("ANNOTATION", "")
    never_cut = CONTROL_NO_CUT in f"{record.get('CATEGORY', '')} {label}".upper()
    raw = _raw_extent(block, spec.layer_for("boundary"))
    if raw is None or min(raw) <= 0.0:
        return ControlPiece(
            block.name,
            label,
            raw or (0.0, 0.0),
            never_cut=never_cut,
            advertised=advertised,
            problem="it has no measurable boundary to compare its label against",
        )
    size = _parse_control_label(label)
    if size is None:
        return ControlPiece(
            block.name,
            label,
            raw,
            never_cut=never_cut,
            advertised=advertised,
            problem=f"its label {label!r} states no size in a unit that can be "
            f'read without guessing (a size needs ", in, cm or mm)',
        )
    drawn_ratio, claimed_ratio = raw[0] / raw[1], size[0] / size[1]
    if abs(drawn_ratio - claimed_ratio) > CONTROL_ASPECT_TOLERANCE * claimed_ratio:
        return ControlPiece(
            block.name,
            label,
            raw,
            size,
            never_cut=never_cut,
            advertised=advertised,
            problem=f"it is drawn {drawn_ratio:.3f}:1 but its label claims "
            f"{claimed_ratio:.3f}:1, further apart than "
            f"{CONTROL_ASPECT_TOLERANCE:.0%}",
        )
    return ControlPiece(block.name, label, raw, size, size[0] / raw[0], never_cut, advertised)


def _find_control_pieces(doc, spec: Dialect) -> list[ControlPiece]:
    """Every block that says it is not a garment piece, measured.

    `DO NOT CUT` is an instruction from the file's author and is obeyed
    whether or not the piece turns out to be usable as a scale reference;
    `CONTROL` in a piece name is only a candidate, and a candidate that fails
    to verify stays an ordinary panel rather than being silently dropped.
    """
    found: list[ControlPiece] = []
    for block in doc.blocks:
        if block.name.startswith("*"):
            continue
        record = _system_text(block)
        marks = f"{record.get('PIECE NAME', '')} {record.get('CATEGORY', '')}".upper()
        label = record.get("ANNOTATION", "")
        advertised = CONTROL_NAME in marks or _CONTROL_LABEL.search(label) is not None
        if CONTROL_NO_CUT not in marks and CONTROL_NAME not in marks:
            continue
        found.append(_measure_control(block, spec, record, advertised=advertised))
    return found


def read_dxf(
    path: str | Path,
    *,
    flavour: str = "astm",
    strict: bool = True,
    units_mm: float | None = None,
) -> tuple[Pattern, ReadReport]:
    """Read a pattern DXF. Unknown layers refuse by CONTENT unless `strict=False`.

    The drawing unit is resolved in this order, and the report says which
    won: an explicit `units_mm` (millimetres per drawing unit); a CONTROL
    PIECE, measured; a non-zero `$INSUNITS`; the header's "UNITS: METRIC /
    ENGLISH" system text (an R12 file - every CLO, Gerber and Lectra export
    - has no `$INSUNITS` at all); else millimetres, with a note. The control
    piece outranks `$INSUNITS` because it is the only rung that can be
    checked against the drawing, and one real writer declares a unit that is
    39.37x wrong; when they disagree the measured square wins and
    `ReadReport.units_conflict` reports the disagreement instead of hiding
    it. A control piece is never returned as a garment panel: `DO NOT CUT`
    means it. Piece boundaries may be LWPOLYLINE or the
    R12 heavy POLYLINE. Layers 84-87 are the standard's quality-validation
    curves - a dense copy of the writer's curves, not geometry to cut - so
    they are counted, measured against the boundary they validate, and never
    imported as internal lines. When the file carries a closed sew line
    (layer 14) the outline is the cut line and the panel says so
    (`meta["outline_is"]`), with the allowance measured between the two.

    A layer no dialect defines is censused, not counted: what entity types
    sit on it, across how many pieces, and how many of its polylines close
    (see `ReadReport`). `strict=True` refuses with that census and asks what
    the layer is - it never guesses a mapping. `strict=False` skips the
    layer but keeps the census AND says so in `notes`, because leniency that
    stays quiet teaches nobody. `observed_layers` is the other side: which
    of the layers the dialect DOES define this file exercised.
    """
    spec = dialect(flavour)
    source = Path(path)
    doc = ezdxf.readfile(source)
    insunits = int(doc.header.get("$INSUNITS", 0) or 0)
    header = _system_text(doc.modelspace())
    report = ReadReport(insunits=insunits, header=header)
    # the control piece has to be measured in DRAWING units, before a scale
    # exists, because measuring it is how the scale is found
    controls = _find_control_pieces(doc, spec)
    scale, units_source = _resolve_units(units_mm, insunits, header, controls, report)
    report.scale_mm, report.units_source = scale, units_source
    # a scale square is metadata: DO NOT CUT means it, and a verified control
    # piece is not a garment panel either. A candidate that failed to verify
    # stays a panel rather than being dropped on a guess.
    not_garments = {c.block for c in controls if c.never_cut or c.mm_per_unit is not None}

    panels: list[Panel] = []
    for block in doc.blocks:
        if block.name.startswith("*"):  # *Model_Space / *Paper_Space are not pieces
            report.skipped_blocks.append(block.name)
            continue
        if block.name in not_garments:
            report.skipped_blocks.append(block.name)
            continue
        panel = _read_piece(block, spec, scale, report)
        if panel is not None:
            panels.append(panel)

    report.observed_layers.sort(key=_layer_order)
    if report.unknown_layers:
        listed = "; ".join(
            _describe_unknown(layer, census)
            for layer, census in sorted(
                report.unknown_layers.items(), key=lambda kv: _layer_order(kv[0])
            )
        )
        if strict:
            raise DxfDialectError(
                f"{source.name}: {listed} - not defined by the {spec.name!r} dialect "
                f"({spec.source}). seamkiln will not guess what a layer means: say what "
                f"these hold and the table can carry them. Re-read with the other dialect, "
                f"or pass strict=False to skip them and keep the census. "
                f"Known layers: {sorted(spec.layers.values())}."
            )
        # lenient is not silent: a caller who chose to skip still learns what
        # was dropped, because a file nobody looked at teaches nobody anything
        report.notes.append(
            f"skipped, not defined by the {spec.name!r} dialect: {listed}. "
            f"ReadReport.unknown_layers holds the census; naming them grows the table."
        )

    report.pieces = len(panels)
    if panels:
        longest = max(max(p.bbox[2] - p.bbox[0], p.bbox[3] - p.bbox[1]) for p in panels)
        low, high = PLAUSIBLE_PIECE_MM
        if not low <= longest <= high:
            report.notes.append(
                f"the largest piece is {longest:.0f} mm across after reading the "
                f"unit as {units_source}; pass units_mm= if that is wrong"
            )
    pattern = Pattern(
        name=header.get("STYLE NAME") or source.stem,
        panels=panels,
        units="mm",
        provenance={
            "source": str(source),
            "dialect": spec.name,
            "dialect_verified": spec.verified,
            "observed_layers": report.observed_layers,
            "insunits": insunits,
            "insunits_note": "0 = undeclared" if insunits == 0 else "",
            "scale_mm_per_unit": scale,
            "units_source": units_source,
            "units_conflict": report.units_conflict,
            "header": header,
            "dxfversion": doc.dxfversion,
            "validation_curves": report.validation_curves,
            "qv_deviation_mm": report.qv_deviation_mm,
        },
    )
    return pattern, report


def _declared_units(insunits: int, header: dict[str, str]) -> tuple[float | None, str, str]:
    """What the file SAYS its unit is - a claim, not a measurement.

    Returns (millimetres per drawing unit or None, which rung said so, the
    complaint to raise if this rung is the one we end up standing on). The
    complaint is deferred rather than raised because a control piece outranks
    this: a file whose header is unreadable but whose control square is
    perfectly clear is a file we can read correctly, and refusing it would
    block work seamkiln can do.
    """
    if insunits:
        if insunits not in INSUNITS_TO_MM:
            return (
                None,
                f"$INSUNITS {insunits}",
                f"$INSUNITS {insunits} is not a length unit seamkiln reads "
                f"(known: {sorted(INSUNITS_TO_MM)}); pass units_mm= explicitly",
            )
        return INSUNITS_TO_MM[insunits], f"$INSUNITS {insunits}", ""
    declared = header.get("UNITS", "").strip().upper()
    if declared:
        if declared not in HEADER_UNITS_TO_MM:
            return (
                None,
                f"header UNITS: {declared}",
                f"header says 'UNITS: {declared}', which seamkiln does not read "
                f"(known: {', '.join(sorted(HEADER_UNITS_TO_MM))}); pass units_mm= explicitly",
            )
        return HEADER_UNITS_TO_MM[declared], f"header UNITS: {declared}", ""
    return None, "undeclared; read as mm", ""


def _resolve_units(
    units_mm: float | None,
    insunits: int,
    header: dict[str, str],
    controls: list[ControlPiece],
    report: ReadReport,
) -> tuple[float, str]:
    """The unit ladder, strongest rung first.

    An explicit caller, then the control piece MEASURED, then `$INSUNITS`,
    then the header's `UNITS:` text, then millimetres with a note. The
    control piece sits above `$INSUNITS` because it is the only rung that can
    be checked against the drawing itself; the rest are claims. When the two
    disagree the control piece wins and the disagreement is reported loudly -
    not refused, because we are not uncertain, and not passed over, because a
    file whose own square contradicts its header is broken and its owner has
    to be told.
    """
    if units_mm is not None:
        if units_mm <= 0.0:
            raise ValueError(f"units_mm must be millimetres per drawing unit, got {units_mm!r}")
        return float(units_mm), "units_mm argument"

    declared, declared_source, complaint = _declared_units(insunits, header)
    measured = next((c for c in controls if c.mm_per_unit is not None), None)
    for control in controls:
        if control.problem and control.advertised:
            report.notes.append(
                f"block {control.block} looks like a control piece but {control.problem}; "
                f"the unit came from the next rung down instead"
            )

    if measured is not None:
        report.control_piece = measured.summary()
        if declared is not None and not _same_scale(declared, measured.mm_per_unit):
            ratio = declared / measured.mm_per_unit
            report.units_conflict = {
                "declared": declared_source,
                "declared_mm_per_unit": declared,
                "measured_mm_per_unit": measured.mm_per_unit,
                "ratio": round(ratio, 4),
                "won": "control piece",
            }
            report.notes.append(
                f"the control piece {measured.block!r} is labelled {measured.label!r} and is "
                f"drawn {measured.raw[0]:.4f} units wide, so one unit is "
                f"{measured.mm_per_unit} mm - but the file declares {declared_source} = "
                f"{declared} mm, which is wrong by a factor of {ratio:.2f}. The measured "
                f"square wins; this file's own unit declaration cannot be trusted."
            )
        return measured.mm_per_unit, f"control piece {measured.block!r} ({measured.label})"

    if complaint:
        raise ValueError(complaint)
    if declared is None:
        return 1.0, "undeclared; read as mm"
    return declared, declared_source


def _same_scale(a: float, b: float) -> bool:
    """Two unit claims agree when they agree to a part in a million."""
    return abs(a - b) <= 1e-6 * max(abs(a), abs(b))


def _layer_order(layer: str) -> tuple[int, str]:
    """Sort layers as the numbers they are: 9 before 82, not after."""
    text = str(layer).strip()
    return (int(text), "") if text.isdigit() else (10**6, text)


def _note_unknown(report: ReadReport, layer: str, entity, *, first_in_block: bool) -> None:
    """Census one entity on a layer no dialect defines.

    A tally cannot say what a layer IS, and that is the whole problem: ten
    of the eighteen ASTM layers are defined from a published description and
    have never been seen in a real file. So record what is actually there -
    the entity types and their counts, how many pieces carry the layer, and
    how many of its polylines are closed, because a closed run is a cut or a
    sew line and an open one is not. All JSON-safe scalars: this rides in a
    report a model may read. Nothing here is ever promoted into the table.
    """
    census = report.unknown_layers.setdefault(layer, {"entities": {}, "pieces": 0})
    kind = entity.dxftype()
    census["entities"][kind] = census["entities"].get(kind, 0) + 1
    if first_in_block:
        census["pieces"] += 1
    if kind in ("LWPOLYLINE", "POLYLINE"):
        closed = bool(entity.closed) if kind == "LWPOLYLINE" else bool(entity.is_closed)
        if closed:
            census["closed"] = census.get("closed", 0) + 1


def _describe_unknown(layer: str, census: dict[str, Any]) -> str:
    """One short line a human can answer from looking at their own pattern."""
    holds = ", ".join(f"{count} {kind}" for kind, count in sorted(census["entities"].items()))
    closed = f" ({census['closed']} closed)" if census.get("closed") else ""
    pieces = census["pieces"]
    return f"layer {layer} holds {holds}{closed} across {pieces} piece{'' if pieces == 1 else 's'}"


def _system_text(space) -> dict[str, str]:
    """`KEY: value` TEXT entities, first one of each key wins."""
    found: dict[str, str] = {}
    for entity in space:
        kind = entity.dxftype()
        if kind not in ("TEXT", "MTEXT"):
            continue
        text = entity.dxf.text if kind == "TEXT" else entity.text
        match = _SYSTEM_TEXT.match(text or "")
        if match:
            found.setdefault(match.group(1).strip().upper(), match.group(2))
    return found


def _polyline_points(entity, scale: float) -> tuple[Polyline, bool]:
    """LWPOLYLINE and the R12 heavy POLYLINE, as one thing."""
    if entity.dxftype() == "LWPOLYLINE":
        raw = [(float(x), float(y)) for x, y, *_ in entity.get_points()]
        closed = bool(entity.closed)
    else:
        raw = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in entity.vertices]
        closed = bool(entity.is_closed)
    return [Vertex(x * scale, y * scale, VertexKind.CURVE) for x, y in raw], closed


def _read_piece(block, spec: Dialect, scale: float, report: ReadReport) -> Panel | None:
    boundaries: list[Polyline] = []
    turn_points: set[tuple[float, float]] = set()
    curve_points: set[tuple[float, float]] = set()
    internals: list[InternalLine] = []
    marks: list[Mark] = []
    validation: list[Polyline] = []
    meta: dict[str, Any] = {}
    annotations: list[str] = []
    name = block.name
    named = False
    unknown_here: set[str] = set()

    for entity in block:
        layer = entity.dxf.layer
        feature = spec.feature_for(layer)
        if feature is None:
            if layer not in ("0", "Defpoints"):
                _note_unknown(report, layer, entity, first_in_block=layer not in unknown_here)
                unknown_here.add(layer)
            continue
        if layer not in report.observed_layers:
            # a layer the dialect defines AND this file actually uses; the
            # ones missing from here are defined on paper and unwitnessed
            report.observed_layers.append(layer)

        kind = entity.dxftype()
        if kind in ("LWPOLYLINE", "POLYLINE"):
            if kind == "POLYLINE" and (entity.is_polygon_mesh or entity.is_poly_face_mesh):
                report.notes.append(f"block {block.name}: a polyface mesh on layer {layer} skipped")
                continue
            points, closed = _polyline_points(entity, scale)
            if feature == "boundary":
                boundaries.append(points)
            elif feature in _QV_FEATURES:
                report.validation_curves += 1
                if feature == "qv_boundary":
                    validation.append(points)
            else:
                line_kind = next(
                    (k for k, f in _LINE_FEATURE.items() if f == feature), LineKind.INTERNAL
                )
                internals.append(InternalLine(line_kind, points, closed=closed))
        elif kind == "POINT":
            location = entity.dxf.location
            spot = (round(float(location.x) * scale, 6), round(float(location.y) * scale, 6))
            if feature == "turn_point":
                turn_points.add(spot)
            elif feature == "curve_point":
                curve_points.add(spot)
            else:
                mark_kind = next(
                    (k for k, f in _MARK_FEATURE.items() if f == feature), MarkKind.NOTCH_SLIT
                )
                marks.append(Mark(mark_kind, spot[0], spot[1]))
        elif kind in ("TEXT", "MTEXT"):
            text = (entity.dxf.text if kind == "TEXT" else entity.text) or ""
            match = _SYSTEM_TEXT.match(text)
            if match:
                key, value = match.group(1).strip().upper(), match.group(2)
                if key == "PIECE NAME":
                    name, named = value or block.name, True
                else:
                    meta.setdefault(key.lower().replace(" ", "_"), value)
            elif text.strip().startswith("#"):
                meta.setdefault("piece_number", text.strip().lstrip("#").strip())
            elif feature in ("text", "annotation"):
                annotations.append(text)
            elif text.strip() and not named:
                name = text.strip()  # seamkiln's own writer: the bare piece name
        elif kind == "LINE":
            start, end = entity.dxf.start, entity.dxf.end
            line_kind = next(
                (k for k, f in _LINE_FEATURE.items() if f == feature), LineKind.INTERNAL
            )
            internals.append(
                InternalLine(
                    line_kind,
                    [
                        Vertex(float(start.x) * scale, float(start.y) * scale),
                        Vertex(float(end.x) * scale, float(end.y) * scale),
                    ],
                )
            )

    if not boundaries:
        return None
    if len(boundaries) > 1:
        boundaries.sort(key=area, reverse=True)
        report.notes.append(
            f"block {block.name}: {len(boundaries)} boundary polylines; the largest is the piece"
        )
    boundary = boundaries[0]
    if annotations:
        meta["annotations"] = annotations

    allowance = 0.0
    sew = next((i for i in internals if i.kind is LineKind.SEW and i.closed), None)
    if sew is not None:
        # the file keeps both lines: the boundary (layer 1) is the cut line
        # and the sew line is the piece; the allowance is their distance
        allowance = _median_offset_mm(sew.points, boundary)
        meta["outline_is"] = "cut_line"
    if validation:
        deviation = max(_max_offset_mm(curve, boundary) for curve in validation)
        meta["qv_deviation_mm"] = round(deviation, 3)
        report.qv_deviation_mm = max(report.qv_deviation_mm, deviation)

    return Panel(
        id=block.name,
        name=name,
        outline=_retag_from_points(boundary, turn_points, curve_points),
        internals=internals,
        marks=marks,
        seam_allowance_mm=allowance,
        meta=meta,
    )


def _ring(outline: Polyline) -> LinearRing:
    return LinearRing([(v.x, v.y) for v in outline])


def _median_offset_mm(points: Polyline, boundary: Polyline) -> float:
    ring = _ring(boundary)
    distances = sorted(ring.distance(Point(v.x, v.y)) for v in points)
    return round(float(distances[len(distances) // 2]), 3) if distances else 0.0


def _max_offset_mm(points: Polyline, boundary: Polyline) -> float:
    ring = _ring(boundary)
    return max((float(ring.distance(Point(v.x, v.y))) for v in points), default=0.0)


def _retag_from_points(
    boundary: Polyline,
    turn_points: set[tuple[float, float]],
    curve_points: set[tuple[float, float]],
) -> Polyline:
    """Restore turn/curve tags from the standard's own layer-2/3 points.

    This is why the round-trip is lossless rather than approximate: the tags
    are read back from the file, not re-inferred from the geometry. A vertex
    named on neither layer keeps the conservative reading - a corner - since
    smoothing a real corner changes the piece and hardening a smooth point
    does not.
    """
    out: Polyline = []
    for vertex in boundary:
        spot = (round(vertex.x, 6), round(vertex.y, 6))
        if spot in curve_points and spot not in turn_points:
            out.append(Vertex(vertex.x, vertex.y, VertexKind.CURVE))
        else:
            out.append(Vertex(vertex.x, vertex.y, VertexKind.TURN))
    return out
