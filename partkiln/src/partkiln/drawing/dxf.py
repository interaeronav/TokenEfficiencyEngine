"""The DXF writer: ezdxf, with REAL `DIMENSION` entities.

A drawing exported as lines and text is a picture; a drawing exported with
`DIMENSION` entities is data a CAD system can re-measure. Every dimension here
therefore goes out through `msp.add_linear_dim` / `add_diameter_dim` /
`add_radius_dim` / `add_angular_dim_2l` followed by `.render()`, so a reader
gets the number back from the geometry:

    ezdxf 1.4.4, verified on this machine - `DIMENSION.get_measurement()`
    returns 100.0 for a horizontal linear dim, 10.0 for
    `add_diameter_dim(radius=5)` and 45.0 for `add_angular_dim_2l`.

One measured wrinkle, recorded rather than papered over: ezdxf's own
`linear_measurement` rotates the two defpoints by the dimension's angle, and
`math.cos(math.radians(90))` is 6.1e-17, so a VERTICAL 60 mm dimension reads
59.999999999999986 - five ulp, from ezdxf's arithmetic, not from ours. The
defpoints themselves are exact: every coordinate this module emits is rounded
to six decimals first (`_p`), so `(160.0, 120.5) -> (160.0, 180.5)` is exactly
60 mm apart in the file. `add_aligned_dim` was tried and rewrites to the same
rotated linear dim, so it does not help.

`$INSUNITS = 4` states millimetres in the header, which is the only place a DXF
can carry a unit; the layers are the ones a shop expects - VISIBLE, HIDDEN
(dashed linetype), DIMS, HATCH, TITLE.

Determinism (rule 7): a fresh `ezdxf` document stamps `$TDCREATE`, `$TDUPDATE`,
`$TDINDWG` and two GUIDs, which would make two identical drawings differ byte
for byte. They are pinned to fixed values here, because a drawing is derived
data - the same model must write the same file, and the timestamp of the run is
not part of the part.
"""

from __future__ import annotations

import contextlib
import io
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from partkiln.document import CommandError
from partkiln.drawing.dims import Dimension, arrow_polygon, place
from partkiln.drawing.hlr import Arc, Polyline, Prim, Segment
from partkiln.drawing.views import (
    LABEL_MM,
    TEXT_MM,
    Drawing,
    frame_lines,
    projection_symbol,
    title_lines,
)

LAYERS: tuple[tuple[str, int, str], ...] = (
    ("VISIBLE", 7, "CONTINUOUS"),
    ("HIDDEN", 8, "DASHED"),
    ("DIMS", 5, "CONTINUOUS"),
    ("HATCH", 8, "CONTINUOUS"),
    ("TITLE", 7, "CONTINUOUS"),
)

# A fixed epoch so two runs of the same model write the same bytes. 2026-09-02
# 00:00 UT as a Julian day number, the DXF header's own clock.
_FIXED_JULIAN = 2461285.5
_FIXED_GUID = "{00000000-0000-0000-0000-000000000000}"
_FIXED_STAMP = "2026-09-02T00:00:00+00:00"
# ezdxf stamps a fresh `$VERSIONGUID` and an "<version> @ <ISO timestamp>" meta
# record at WRITE time, after every hook this module has. Both are normalised in
# the emitted text so rule 7 is literally true: same model, same bytes.
_META_RE = re.compile(r"^(\S+ @ )\d{4}-\d{2}-\d{2}T[0-9:.+\-]+$", re.M)
_GUID_RE = re.compile(r"(\$(?:VERSION|FINGERPRINT)GUID\r?\n\s*2\r?\n)\{[0-9A-Fa-f-]+\}")


def _p(x: float, y: float) -> tuple[float, float]:
    """One point, rounded to the six decimals a DXF is read at.

    Without this the vertical extent of a 60 mm plate arrives as
    59.999999999999986 through the float chain and `get_measurement()` says so.
    """
    return (round(float(x), 6) + 0.0, round(float(y), 6) + 0.0)


def _prim(msp: Any, prim: Prim, layer: str) -> None:
    if isinstance(prim, Segment):
        msp.add_line(_p(prim.x0, prim.y0), _p(prim.x1, prim.y1), dxfattribs={"layer": layer})
    elif isinstance(prim, Arc):
        if prim.full:
            msp.add_circle(_p(prim.cx, prim.cy), round(prim.r, 6), dxfattribs={"layer": layer})
        else:
            msp.add_arc(
                _p(prim.cx, prim.cy),
                round(prim.r, 6),
                round(prim.a0, 6),
                round(prim.a1, 6),
                dxfattribs={"layer": layer},
            )
    elif isinstance(prim, Polyline):
        msp.add_lwpolyline([_p(x, y) for x, y in prim.points], dxfattribs={"layer": layer})


def _text(msp: Any, x: float, y: float, text: str, size: float, layer: str) -> None:
    entity = msp.add_text(text, height=round(size, 6), dxfattribs={"layer": layer})
    entity.set_placement(_p(x, y))


def _dimension(msp: Any, spec: dict[str, Any], override: str | None) -> None:
    """One real `DIMENSION`.

    `override` prefixes the printed string when the dimension carries a count
    the measurement cannot (`4x <>` prints "4x 6.6"); `<>` is ezdxf's
    placeholder for the measured value, so the MEASUREMENT still comes from the
    geometry and `get_measurement()` is unaffected.
    """
    kind = spec.get("kind")
    extra: dict[str, Any] = {"layer": "DIMS"}
    if override:
        extra["text"] = override
    if kind == "linear":
        dim = msp.add_linear_dim(
            base=_p(*spec["base"]),
            p1=_p(*spec["p1"]),
            p2=_p(*spec["p2"]),
            angle=float(spec.get("angle", 0.0)),
            dimstyle="EZDXF",
            dxfattribs=extra,
        )
    elif kind == "dia":
        dim = msp.add_diameter_dim(
            center=_p(*spec["centre"]),
            radius=round(float(spec["radius"]), 6),
            angle=float(spec.get("angle", 45.0)),
            dimstyle="EZ_RADIUS",
            dxfattribs=extra,
        )
    elif kind == "rad":
        dim = msp.add_radius_dim(
            center=_p(*spec["centre"]),
            radius=round(float(spec["radius"]), 6),
            angle=float(spec.get("angle", 45.0)),
            dimstyle="EZ_RADIUS",
            dxfattribs=extra,
        )
    elif kind == "angular":
        dim = msp.add_angular_dim_2l(
            base=_p(*spec["base"]),
            line1=(_p(*spec["line1"][0]), _p(*spec["line1"][1])),
            line2=(_p(*spec["line2"][0]), _p(*spec["line2"][1])),
            dimstyle="EZ_CURVED",
            dxfattribs=extra,
        )
    else:
        return
    dim.render()


def _annotation(msp: Any, dim: Dimension, drawing: Drawing) -> None:
    """A real DIMENSION where ezdxf has one, the exploded picture where it does
    not (ordinate chains, chamfer notes): lines, arrowheads and text on DIMS."""
    geo = place(drawing.view(dim.view), dim)
    specs = geo.dxf.get("chain") or ([geo.dxf] if geo.dxf.get("kind") else [])
    count = int(dim.extra.get("count") or 0)
    override = f"{count}x <>" if count > 1 else None
    if specs:
        for spec in specs:
            _dimension(msp, spec, override)
        return
    for line in geo.lines:
        msp.add_line(_p(line.x0, line.y0), _p(line.x1, line.y1), dxfattribs={"layer": "DIMS"})
    for tip, angle in geo.arrows:
        msp.add_solid(
            [_p(x, y) for x, y in arrow_polygon(tip, angle)], dxfattribs={"layer": "DIMS"}
        )
    for x, y, text, size, _rotation in geo.texts:
        _text(msp, x, y, text, size, "DIMS")


def _table(
    msp: Any,
    x: float,
    y: float,
    heading: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    widths: Sequence[float],
    row_mm: float = 5.0,
) -> float:
    _text(msp, x, y, heading, TEXT_MM, "TITLE")
    cursor = y - row_mm
    at = x
    for column, width in zip(columns, widths, strict=True):
        _text(msp, at, cursor, column, TEXT_MM * 0.85, "TITLE")
        at += width
    cursor -= row_mm
    for row in rows:
        at = x
        for cell, width in zip(row, widths, strict=True):
            _text(msp, at, cursor, str(cell), TEXT_MM * 0.85, "TITLE")
            at += width
        cursor -= row_mm
    return cursor - row_mm


def build(drawing: Drawing) -> Any:
    """The ezdxf document for this sheet (kept out of `write` so a test can read
    the entities without a temporary file)."""
    try:
        import ezdxf
    except ImportError as exc:  # pragma: no cover - ezdxf is a core dependency
        raise CommandError(
            "ezdxf is not installed, so partkiln cannot write DXF. Fix: pip install ezdxf.",
            code="pk_not_served",
        ) from exc

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4  # millimetres - the only unit a DXF can declare
    doc.header["$MEASUREMENT"] = 1
    for key in ("$TDCREATE", "$TDUPDATE", "$TDUCREATE", "$TDUUPDATE"):
        with contextlib.suppress(Exception):  # older headers lack the UT twins
            doc.header[key] = _FIXED_JULIAN
    doc.header["$TDINDWG"] = 0.0
    for key in ("$FINGERPRINTGUID", "$VERSIONGUID"):
        doc.header[key] = _FIXED_GUID
    for name, colour, linetype in LAYERS:
        if name not in doc.layers:
            doc.layers.add(name, color=colour, linetype=linetype)

    msp = doc.modelspace()
    for line in frame_lines(drawing.sheet):
        _prim(msp, line, "TITLE")
    for prim in projection_symbol(drawing):
        _prim(msp, prim, "TITLE")

    for view in drawing.views:
        for prim in view.sheet_prims(view.visible):
            _prim(msp, prim, "VISIBLE")
        for prim in view.sheet_prims(view.hidden):
            _prim(msp, prim, "HIDDEN")
        for prim in view.sheet_prims(view.hatch):
            _prim(msp, prim, "HATCH")
        if view.window is not None and view.kind != "detail":
            cx, cy, r = view.window
            p = view.to_sheet((cx, cy))
            msp.add_circle(p, r * view.scale, dxfattribs={"layer": "DIMS"})
        x0, y0, x1, _y1 = view.sheet_bbox()
        _text(msp, 0.5 * (x0 + x1), y0 - 6.0 - LABEL_MM, view.label.upper(), LABEL_MM, "TITLE")

    for dim in drawing.dims:
        _annotation(msp, dim, drawing)

    tx = drawing.sheet.margin + 2.0
    ty = drawing.sheet.height - drawing.sheet.margin - 6.0
    if drawing.holes:
        shown = drawing.holes[: drawing.holes_shown or len(drawing.holes)]
        rows: list[Sequence[Any]] = [
            (r["name"], r["x"], r["y"], r["dia_mm"], r["depth"]) for r in shown
        ]
        if len(shown) < len(drawing.holes):
            rows.append((f"+{len(drawing.holes) - len(shown)} more", "", "", "", ""))
        ty = _table(
            msp,
            tx,
            ty,
            f"HOLE TABLE ({len(drawing.holes)})",
            ("TAG", "X", "Y", "DIA", "DEPTH"),
            rows,
            (26.0, 16.0, 16.0, 14.0, 16.0),
        )
    if drawing.parts:
        ty = _table(
            msp,
            tx,
            ty,
            f"PARTS LIST ({len(drawing.parts)})",
            ("ITEM", "PART", "QTY", "MATERIAL", "MASS g"),
            [
                (r["item"], r["part"], r["qty"], r["material"], r.get("total_g", 0.0))
                for r in drawing.parts
            ],
            (14.0, 34.0, 12.0, 30.0, 20.0),
        )
    for i, note in enumerate(drawing.notes):
        _text(msp, tx, ty - i * 5.0, note, TEXT_MM, "TITLE")

    for x, y, text, size in title_lines(drawing):
        _text(msp, x, y, text, size, "TITLE")
    return doc


def render(drawing: Drawing) -> str:
    """The DXF text, with ezdxf's two write-time stamps normalised (rule 7)."""
    stream = io.StringIO()
    build(drawing).write(stream)
    text = _META_RE.sub(rf"\g<1>{_FIXED_STAMP}", stream.getvalue())
    return _GUID_RE.sub(rf"\g<1>{_FIXED_GUID}", text)


def write(drawing: Drawing, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(drawing), encoding="utf-8")
    return destination


__all__ = ["LAYERS", "build", "render", "write"]
