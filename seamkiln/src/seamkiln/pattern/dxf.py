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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ezdxf

from seamkiln.pattern.geometry import Polyline, Vertex, VertexKind
from seamkiln.pattern.model import InternalLine, LineKind, Mark, MarkKind, Panel, Pattern

# $INSUNITS -> millimetres per drawing unit. 0 is "unitless", which is not a
# unit but a missing declaration, and is treated as mm with a provenance note.
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


@dataclass
class ReadReport:
    pieces: int = 0
    unknown_layers: dict[str, int] = field(default_factory=dict)
    skipped_blocks: list[str] = field(default_factory=list)
    scale_mm: float = 1.0
    insunits: int = 0


def read_dxf(
    path: str | Path, *, flavour: str = "astm", strict: bool = True
) -> tuple[Pattern, ReadReport]:
    """Read a pattern DXF. Unknown layers refuse by name unless `strict=False`."""
    spec = dialect(flavour)
    source = Path(path)
    doc = ezdxf.readfile(source)
    insunits = int(doc.header.get("$INSUNITS", 0) or 0)
    scale = INSUNITS_TO_MM.get(insunits, 1.0)
    report = ReadReport(scale_mm=scale, insunits=insunits)

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
    pattern = Pattern(
        name=source.stem,
        panels=panels,
        units="mm",
        provenance={
            "source": str(source),
            "dialect": spec.name,
            "dialect_verified": spec.verified,
            "insunits": insunits,
            "insunits_note": "0 = undeclared; read as mm" if insunits == 0 else "",
            "scale_mm_per_unit": scale,
            "dxfversion": doc.dxfversion,
        },
    )
    return pattern, report


def _read_piece(block, spec: Dialect, scale: float, report: ReadReport) -> Panel | None:
    boundary: Polyline | None = None
    turn_points: set[tuple[float, float]] = set()
    curve_points: set[tuple[float, float]] = set()
    internals: list[InternalLine] = []
    marks: list[Mark] = []
    name = block.name

    for entity in block:
        layer = entity.dxf.layer
        feature = spec.feature_for(layer)
        if feature is None:
            if layer not in ("0", "Defpoints"):
                report.unknown_layers[layer] = report.unknown_layers.get(layer, 0) + 1
            continue

        kind = entity.dxftype()
        if kind == "LWPOLYLINE":
            points = [
                Vertex(float(x) * scale, float(y) * scale, VertexKind.CURVE)
                for x, y, *_ in entity.get_points()
            ]
            if feature == "boundary":
                boundary = points
            else:
                line_kind = next(
                    (k for k, f in _LINE_FEATURE.items() if f == feature), LineKind.INTERNAL
                )
                internals.append(InternalLine(line_kind, points, closed=bool(entity.closed)))
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
            name = (entity.dxf.text if kind == "TEXT" else entity.text) or block.name
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

    if boundary is None:
        return None
    return Panel(
        id=block.name,
        name=name,
        outline=_retag_from_points(boundary, turn_points, curve_points),
        internals=internals,
        marks=marks,
    )


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
