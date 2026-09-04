"""DXF pattern interchange: the AAMA and ASTM dialects, on ezdxf (MIT).

ASTM D6673 - "Standard Practice for Sewn Products Pattern Data Interchange"
- **was withdrawn in 2019** and is still what the industry exchanges. It is
based on AutoCAD DXF R13, stores one style per file, uses **one BLOCK per
pattern piece**, and assigns features to 23 predefined layers. AAMA
published its own mapping first; the two are close cousins that number some
layers differently, so this module keeps the mapping as DATA (`Dialect`)
rather than as code, and every entry carries where it came from.

Three measured facts shape the implementation (2026-09-01, ezdxf 1.4.4):

  1. **ezdxf cannot write R13** - `Unsupported DXF version "AC1012"`. R2000
     is the nearest version it will write, so that is what we write, and
     `provenance["dxfversion"]` says so rather than implying R13.
  2. **R12 does not export `$INSUNITS`** (ezdxf warns), which would lose the
     unit declaration a pattern absolutely depends on. Another reason for
     R2000.
  3. **Every DXF has `*Model_Space` and `*Paper_Space` blocks.** A strict
     ASTM importer expects every block to be a pattern piece, which is the
     known ezdxf/ASTM friction. The reader skips `*`-prefixed blocks; the
     writer cannot remove them, and says so here rather than in a bug report
     six months from now.

Vertex tags round-trip through the standard itself: layers 2 and 3 hold the
turn points and curve points as POINT entities, so a corner comes back a
corner instead of being re-guessed from angles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ezdxf
from shapely.geometry import LinearRing, Point

from seamkiln.pattern.geometry import Polyline, Vertex, VertexKind, area
from seamkiln.pattern.model import InternalLine, LineKind, Mark, MarkKind, Panel, Pattern

# $INSUNITS -> millimetres per drawing unit. 0 is "unitless", which is not a
# unit but a missing declaration: the reader then asks the header text, and
# only after that falls back to mm with a note (see `_resolve_units`).
INSUNITS_TO_MM: dict[int, float] = {0: 1.0, 1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0}
MM_INSUNITS = 4
POINT_TOLERANCE_MM = 1e-6


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


def write_dxf(pattern: Pattern, path: str | Path, *, flavour: str = "astm") -> dict[str, Any]:
    """Write one style to one file: a block per piece, features on layers."""
    spec = dialect(flavour)
    doc = ezdxf.new(dxfversion="R2000", setup=False)
    doc.header["$INSUNITS"] = MM_INSUNITS
    for number in sorted(spec.layers.values()):
        doc.layers.add(str(number))

    modelspace = doc.modelspace()
    written: dict[str, int] = {}

    for panel in pattern.panels:
        block = doc.blocks.new(_block_name(panel.id))
        # ASTM layer 1 is the PIECE BOUNDARY, which is the cut line. seamkiln
        # holds the sew line as the outline, so the allowance is applied here
        # - and the sew line goes to layer 14, where the standard puts it.
        from seamkiln.pattern.allowance import cut_line

        boundary = cut_line(panel) if panel.seam_allowance_mm else panel.outline
        _add_polyline(block, boundary, spec.layer_for("boundary"), closed=True)
        written["boundary"] = written.get("boundary", 0) + 1
        if panel.seam_allowance_mm:
            _add_polyline(block, panel.outline, spec.layer_for("sew"), closed=True)
            written["sew"] = written.get("sew", 0) + 1

        for vertex in boundary:
            feature = "turn_point" if vertex.kind is VertexKind.TURN else "curve_point"
            block.add_point((vertex.x, vertex.y), dxfattribs={"layer": spec.layer_for(feature)})
            written[feature] = written.get(feature, 0) + 1

        for internal in panel.internals:
            feature = _LINE_FEATURE[internal.kind]
            _add_polyline(block, internal.points, spec.layer_for(feature), closed=internal.closed)
            written[feature] = written.get(feature, 0) + 1

        for mark in panel.marks:
            feature = _MARK_FEATURE[mark.kind]
            block.add_point((mark.x, mark.y), dxfattribs={"layer": spec.layer_for(feature)})
            written[feature] = written.get(feature, 0) + 1

        # Piece System Text: the standard's way of naming a piece, inside its block
        block.add_text(
            panel.name,
            height=10.0,
            dxfattribs={"layer": spec.layer_for("boundary")},
        ).set_placement((panel.bbox[0], panel.bbox[1]))
        modelspace.add_blockref(block.name, (0.0, 0.0))

    destination = Path(path)
    doc.saveas(destination)
    return {
        "path": str(destination),
        "dialect": spec.name,
        "dialect_verified": spec.verified,
        "dxfversion": "R2000",
        "dxfversion_note": "ASTM D6673 is based on R13; ezdxf cannot write R13",
        "pieces": len(pattern.panels),
        "entities": written,
        "layout_blocks_present": ["*Model_Space", "*Paper_Space"],
    }


def _block_name(piece_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in piece_id)
    return safe or "PIECE"


def _add_polyline(block, points: Polyline, layer: str, *, closed: bool) -> None:
    block.add_lwpolyline([(v.x, v.y) for v in points], close=closed, dxfattribs={"layer": layer})


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
_QV_FEATURES = ("qv_boundary", "qv_internal", "qv_cutout", "qv_sew")


@dataclass
class ReadReport:
    pieces: int = 0
    unknown_layers: dict[str, int] = field(default_factory=dict)
    skipped_blocks: list[str] = field(default_factory=list)
    scale_mm: float = 1.0
    insunits: int = 0
    units_source: str = ""
    header: dict[str, str] = field(default_factory=dict)
    validation_curves: int = 0
    qv_deviation_mm: float = 0.0
    notes: list[str] = field(default_factory=list)


def read_dxf(
    path: str | Path,
    *,
    flavour: str = "astm",
    strict: bool = True,
    units_mm: float | None = None,
) -> tuple[Pattern, ReadReport]:
    """Read a pattern DXF. Unknown layers refuse by name unless `strict=False`.

    The drawing unit is resolved in this order, and the report says which
    won: an explicit `units_mm` (millimetres per drawing unit); a non-zero
    `$INSUNITS`; the header's "UNITS: METRIC / ENGLISH" system text (an R12
    file - every CLO, Gerber and Lectra export - has no `$INSUNITS` at all);
    else millimetres, with a note. Piece boundaries may be LWPOLYLINE or the
    R12 heavy POLYLINE. Layers 84-87 are the standard's quality-validation
    curves - a dense copy of the writer's curves, not geometry to cut - so
    they are counted, measured against the boundary they validate, and never
    imported as internal lines. When the file carries a closed sew line
    (layer 14) the outline is the cut line and the panel says so
    (`meta["outline_is"]`), with the allowance measured between the two.
    """
    spec = dialect(flavour)
    source = Path(path)
    doc = ezdxf.readfile(source)
    insunits = int(doc.header.get("$INSUNITS", 0) or 0)
    header = _system_text(doc.modelspace())
    scale, units_source = _resolve_units(units_mm, insunits, header)
    report = ReadReport(scale_mm=scale, insunits=insunits, units_source=units_source, header=header)

    panels: list[Panel] = []
    for block in doc.blocks:
        if block.name.startswith("*"):  # *Model_Space / *Paper_Space are not pieces
            report.skipped_blocks.append(block.name)
            continue
        panel = _read_piece(block, spec, scale, report)
        if panel is not None:
            panels.append(panel)

    if strict and report.unknown_layers:
        listed = ", ".join(
            f"layer {layer} ({count} entities)"
            for layer, count in sorted(report.unknown_layers.items())
        )
        raise DxfDialectError(
            f"{source.name}: {listed} not defined by the {spec.name!r} dialect "
            f"({spec.source}). Re-read with the other dialect, or pass strict=False "
            f"to skip them. Known layers: {sorted(spec.layers.values())}."
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
            "insunits": insunits,
            "insunits_note": "0 = undeclared" if insunits == 0 else "",
            "scale_mm_per_unit": scale,
            "units_source": units_source,
            "header": header,
            "dxfversion": doc.dxfversion,
            "validation_curves": report.validation_curves,
            "qv_deviation_mm": report.qv_deviation_mm,
        },
    )
    return pattern, report


def _resolve_units(
    units_mm: float | None, insunits: int, header: dict[str, str]
) -> tuple[float, str]:
    if units_mm is not None:
        if units_mm <= 0.0:
            raise ValueError(f"units_mm must be millimetres per drawing unit, got {units_mm!r}")
        return float(units_mm), "units_mm argument"
    if insunits:
        if insunits not in INSUNITS_TO_MM:
            raise ValueError(
                f"$INSUNITS {insunits} is not a length unit seamkiln reads "
                f"(known: {sorted(INSUNITS_TO_MM)}); pass units_mm= explicitly"
            )
        return INSUNITS_TO_MM[insunits], f"$INSUNITS {insunits}"
    declared = header.get("UNITS", "").strip().upper()
    if declared:
        if declared not in HEADER_UNITS_TO_MM:
            raise ValueError(
                f"header says 'UNITS: {declared}', which seamkiln does not read "
                f"(known: {', '.join(sorted(HEADER_UNITS_TO_MM))}); pass units_mm= explicitly"
            )
        return HEADER_UNITS_TO_MM[declared], f"header UNITS: {declared}"
    return 1.0, "undeclared; read as mm"


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

    for entity in block:
        layer = entity.dxf.layer
        feature = spec.feature_for(layer)
        if feature is None:
            if layer not in ("0", "Defpoints"):
                report.unknown_layers[layer] = report.unknown_layers.get(layer, 0) + 1
            continue

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
