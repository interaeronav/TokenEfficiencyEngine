"""A48 — writing and editing PDFs, without pretending to do the impossible.

TEE could already READ a PDF well: `extract/documents.py` pulls text,
dimension strings and a scale ladder out of one, and `tee_media` renders a
page. It could not write one. The AURA-X chair deliverables were built by
running fpdf2 inline with no script kept - the exact pattern the pipeline
lane exists to end, and the reason `fpdf2` sat in the dev dependency group
rather than anywhere a user could reach it.

Two tools. `pdf_compose` builds a new document from a block list.
`pdf_edit` does page surgery and stamps overlays. Both read A and write B;
neither ever writes to its own input.

**What this deliberately will not do: rewrite the text inside an existing
PDF.** A PDF does not store paragraphs - it stores positioned glyph runs,
often split mid-word across several show-text operators, with the layout
baked in. "Change this sentence" means re-flowing spans whose widths,
kerning and line breaks were decided when the file was made, and the
failure mode is silent: a document that opens fine and is subtly wrong.
`pdf_edit` refuses that by name and says why. Stamping an overlay is the
honest version of editing, and it is what this offers.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

BLOCK_KINDS = ("heading", "paragraph", "image", "table", "page_break", "spacer", "vector")
EDIT_OPS = ("merge", "split", "reorder", "rotate", "delete_pages", "extract_pages", "stamp")

PAGE_W_MM = 210.0  # A4 portrait
MARGIN_MM = 15.0
CONTENT_W_MM = PAGE_W_MM - 2 * MARGIN_MM
HEADING_SIZES = {1: 20, 2: 15, 3: 12}


# A51 P4. The core fonts fpdf2 ships are Latin-1 only, so `pdf_compose` did
# not merely degrade on ordinary prose - it RAISED. Measured before this
# existed:
#
#   ASCII, accents (façade), maths (m² ° ±)   OK
#   curly quotes and em dashes (U+2018-201D, U+2014)  FPDFUnicodeEncodingException
#   Greek, CJK, emoji                          FPDFUnicodeEncodingException
#
# The damaging half is not CJK; it is the quotes and dashes that appear in
# almost any text a model writes or a person pastes from a document. One
# smart quote destroyed a whole report.
#
# Two ways out, and both are offered because they fail differently. Embed a
# font and everything works. Without one, TRANSLITERATE the handful of
# typographic characters Latin-1 lacks - each mapping preserves meaning
# exactly (a curly quote becomes a straight one), and the answer SAYS it
# happened, because a silent substitution is how a document quietly stops
# saying what its author wrote.
TYPOGRAPHIC_FALLBACK = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": ",",
    "\u201b": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u201f": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2015": "-",
    "\u2212": "-",
    "\u2026": "...",
    "\u2022": "-",
    "\u00a0": " ",
    "\u200b": "",
    "\u2039": "<",
    "\u203a": ">",
    "\u00ab": "<<",
    "\u00bb": ">>",
    "\u2032": "'",
    "\u2033": '"',
    "\u02bc": "'",
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2044": "/",
    "\u00ad": "",
}

# Where a system font may be found by name. No font is vendored into the
# repo: Arial Unicode is Apple-licensed and redistribution is not TEE's to
# grant, while using a font already on the owner's machine is unremarkable.
FONT_DIRS = (
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
    str(Path.home() / "Library/Fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
)


def resolve_font(spec: str) -> Path:
    """A path, or a name looked up in the usual font directories."""
    candidate = Path(spec).expanduser()
    if candidate.is_file():
        return candidate
    stem = candidate.name
    for directory in FONT_DIRS:
        base = Path(directory)
        if not base.is_dir():
            continue
        for suffix in ("", ".ttf", ".TTF", ".otf", ".ttc"):
            hit = base / f"{stem}{suffix}"
            if hit.is_file():
                return hit
    raise TeeError(
        "pdf_font_missing",
        f"No font found for {spec!r}.",
        fix="Give a full path to a .ttf/.otf, or a filename present in "
        f"one of: {', '.join(FONT_DIRS[:3])}. On macOS "
        "'Arial Unicode.ttf' covers essentially everything.",
    )


def _degrade(text: str) -> tuple[str, list[str]]:
    """Latin-1-safe text, plus the characters that had to be changed."""
    changed: list[str] = []
    out = []
    for ch in text:
        if ch in TYPOGRAPHIC_FALLBACK:
            changed.append(ch)
            out.append(TYPOGRAPHIC_FALLBACK[ch])
            continue
        try:
            ch.encode("latin-1")
            out.append(ch)
        except UnicodeEncodeError:
            changed.append(ch)
            out.append("?")
    return "".join(out), changed


def _need_fpdf():
    try:
        from fpdf import FPDF

        return FPDF
    except ImportError as exc:
        raise TeeError(
            "pdf_unavailable",
            "Writing PDFs needs fpdf2, which is not installed.",
            fix="uv pip install 'tee-engine[pdf]'",
        ) from exc


def _need_pypdf():
    try:
        import pypdf

        return pypdf
    except ImportError as exc:
        raise TeeError(
            "pdf_unavailable",
            "Editing PDFs needs pypdf, which is not installed.",
            fix="uv pip install 'tee-engine[pdf]'",
        ) from exc


def _out_path(spec: dict[str, Any], key: str = "out") -> Path:
    """An explicit destination that will not clobber anything by accident."""
    raw = str(spec.get(key) or "").strip()
    if not raw:
        raise TeeError(
            "pdf_no_out",
            f"'{key}' is required: name the file to write.",
            fix=f'Pass {{"{key}": "docs/report.pdf"}}. TEE never picks the path for you.',
        )
    out = Path(raw).expanduser()
    if out.exists() and not spec.get("overwrite"):
        raise TeeError(
            "pdf_exists",
            f"{out} already exists.",
            fix="Pass overwrite: true to replace it, or choose another name. "
            "Silently replacing a document someone made is not a default.",
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def _jpeg_bytes(path: Path) -> io.BytesIO:
    """Any image fpdf2 can place - including HEIC, which it cannot read
    itself. v0.11.0's `open_image` door opens it; we hand fpdf2 a JPEG."""
    from tee.kernel.imaging import open_image

    with open_image(path) as img:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=88)
    buf.seek(0)
    return buf


def _colour(doc, value) -> None:
    """A `color` key on a block: [r, g, b] or "#rrggbb". Ignored if absent."""
    if not value:
        return
    doc.set_text_color(*_rgb(value))


# --- A66 gap 7: the vector block -------------------------------------------
#
# A drawing sheet is not prose with a picture pasted into it: it is
# positioned geometry at a stated scale. Until this existed `pk_drawing`
# reached a PDF through partkiln's own optional fpdf2 extra, so TEE's PDF
# lane could not draw the one document TEE's CAD lane makes.
#
# The whole design is a single rule: every coordinate in a vector block is
# read through a STATED frame, and that frame is echoed back in the answer.
# A sheet whose scale is implicit is a sheet that lies - a 1:2 elevation
# printed as 1:1 is not a rendering bug, it is a wrong part.
#
# The frame has four parts, and each is a question a drawing must answer
# out loud:
#
#   units   mm | cm | in | pt - the units of every coordinate below
#   origin  top_left (PDF's own, y down) or bottom_left (CAD's, y up)
#   scale   paper:model - "1:2", "2:1" or a bare 0.5; 1:1 by default
#   at      where this block's (0, 0) sits on the paper, in `units`,
#           UNSCALED, because an insertion point is a fact about paper
#
# What deliberately does NOT pass through the frame: line widths, dash
# lengths, arrowhead sizes and text heights. A 0.35 mm line is 0.35 mm at
# 1:1 and at 1:50 - that is what a line width MEANS to a draughtsman - so
# each of those keys carries its unit in its own name (`width_mm`,
# `dash_mm`, `size_pt`) and is never multiplied by the scale.
#
# Angles (arc sweeps, text rotation) are degrees counter-clockwise in the
# BLOCK's frame, measured from +x. In a bottom_left frame that reads
# counter-clockwise on the paper too; in a top_left frame, where y grows
# downwards, the same number reads clockwise. That is the honest
# consequence of choosing your own frame, not a bug.

VECTOR_ITEM_KINDS = ("line", "polyline", "rect", "circle", "arc", "path", "text")
VECTOR_UNITS_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72.0}
VECTOR_ORIGINS = ("top_left", "bottom_left")

# Paper millimetres, both numbers. Only a two-element dash/gap array is
# expressible here, so a centre line's long-short-long array is refused by
# name rather than silently approximated - see `_dash_mm`.
DASH_PRESETS_MM = {"solid": (0.0, 0.0), "hidden": (2.5, 1.5)}

DEFAULT_LINE_MM = 0.25
DEFAULT_TEXT_PT = 8.0
DEFAULT_ARROW_MM = 3.0

# ISO A series and the US sizes, portrait, in millimetres. A drawing sheet
# is rarely A4 portrait, and the lane hardcoded exactly that.
PAGE_SIZES_MM: dict[str, tuple[float, float]] = {
    "a0": (841.0, 1189.0),
    "a1": (594.0, 841.0),
    "a2": (420.0, 594.0),
    "a3": (297.0, 420.0),
    "a4": (210.0, 297.0),
    "a5": (148.0, 210.0),
    "letter": (215.9, 279.4),
    "legal": (215.9, 355.6),
    "tabloid": (279.4, 431.8),
}


def _page_mm(spec: dict[str, Any]) -> tuple[float, float]:
    """The sheet, in millimetres. Named size or an explicit [w, h]."""
    raw = spec.get("page") or "A4"
    if isinstance(raw, (list, tuple)):
        if len(raw) != 2:
            raise TeeError(
                "pdf_bad_page",
                f"page {list(raw)!r} is not a size.",
                fix='Pass [width_mm, height_mm], or a name: "A3", "letter".',
            )
        try:
            width, height = float(raw[0]), float(raw[1])
        except (TypeError, ValueError) as exc:
            raise TeeError(
                "pdf_bad_page",
                f"page {list(raw)!r} is not two numbers.",
                fix='Pass [420, 297] (millimetres), or a name: "A3".',
            ) from exc
    else:
        key = str(raw).strip().lower().replace(" ", "").replace("-", "")
        if key not in PAGE_SIZES_MM:
            raise TeeError(
                "pdf_bad_page",
                f"'{raw}' is not a page size TEE knows.",
                fix=f"Use one of: {', '.join(sorted(PAGE_SIZES_MM))}; or give "
                "[width_mm, height_mm] outright.",
            )
        width, height = PAGE_SIZES_MM[key]
    if width <= 0 or height <= 0:
        raise TeeError(
            "pdf_bad_page",
            f"a {width} x {height} mm page has no area.",
            fix="Both numbers must be positive millimetres.",
        )
    orientation = str(spec.get("orientation") or "portrait").strip().lower()
    if orientation not in ("portrait", "landscape"):
        raise TeeError(
            "pdf_bad_page",
            f"'{orientation}' is not an orientation.",
            fix='Use "portrait" or "landscape". Landscape swaps whatever '
            "size you named - it does not pick one for you.",
        )
    if orientation == "landscape":
        width, height = height, width
    return width, height


def _scale_factor(value: Any) -> tuple[float, str]:
    """paper:model, as a factor and as the string to print on the sheet."""
    if value in (None, "", 0):
        return 1.0, "1:1"
    if isinstance(value, str):
        text = value.strip().replace(" ", "")
        if ":" in text:
            left, _, right = text.partition(":")
            try:
                paper, model = float(left), float(right)
            except ValueError as exc:
                raise TeeError(
                    "pdf_bad_scale",
                    f"'{value}' is not a scale.",
                    fix='Use "1:2" (half size), "2:1" (twice size) or a bare factor 0.5.',
                ) from exc
            _finite(paper, "pdf_bad_scale", "the left term of the scale", "Use 1:2, 5:1.")
            _finite(model, "pdf_bad_scale", "the right term of the scale", "Use 1:2, 5:1.")
            if paper <= 0 or model <= 0:
                raise TeeError(
                    "pdf_bad_scale",
                    f"'{value}' has a zero or negative term.",
                    fix="Both sides of a scale are positive: 1:2, 5:1.",
                )
            return paper / model, f"{left}:{right}"
        try:
            factor = float(text)
        except ValueError as exc:
            raise TeeError(
                "pdf_bad_scale",
                f"'{value}' is not a scale.",
                fix='Use "1:2", "2:1", or a bare factor such as 0.5.',
            ) from exc
    else:
        factor = float(value)
    _finite(factor, "pdf_bad_scale", "the scale factor", "A scale factor is a finite number.")
    if factor <= 0:
        raise TeeError(
            "pdf_bad_scale",
            f"{factor} is not a scale.",
            fix="A scale factor is positive. 0.5 is half size, 2 is double.",
        )
    return factor, (f"1:{1 / factor:g}" if factor < 1 else f"{factor:g}:1")


def _dash_mm(value: Any) -> tuple[float, float]:
    """A dash pattern in PAPER millimetres: a preset, a number, or [on, off]."""
    if value in (None, "", False):
        return 0.0, 0.0
    if isinstance(value, str):
        key = value.strip().lower()
        if key in DASH_PRESETS_MM:
            return DASH_PRESETS_MM[key]
        raise TeeError(
            "pdf_bad_dash",
            f"'{value}' is not a dash pattern.",
            fix=f"Use {', '.join(sorted(DASH_PRESETS_MM))}, a number (equal dash "
            "and gap, mm), or [dash_mm, gap_mm]. A centre line's long-short-long "
            "array is NOT offered: this backend carries one dash and one gap, so "
            "draw a centre line as explicit `line` items rather than have TEE "
            "approximate a standard pattern behind your back.",
        )
    if isinstance(value, (int, float)):
        one = _finite(float(value), "pdf_bad_dash", f"the dash {value!r}", "[dash_mm, gap_mm].")
        return one, one
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            on, off = float(value[0]), float(value[1])
        except (TypeError, ValueError) as exc:
            raise TeeError(
                "pdf_bad_dash",
                f"{list(value)!r} is not two lengths.",
                fix="[dash_mm, gap_mm], e.g. [2.5, 1.5].",
            ) from exc
        fix = "[dash_mm, gap_mm], both finite, e.g. [2.5, 1.5]."
        return (
            _finite(on, "pdf_bad_dash", "the dash length", fix),
            _finite(off, "pdf_bad_dash", "the gap length", fix),
        )
    raise TeeError(
        "pdf_bad_dash",
        f"{value!r} is not a dash pattern.",
        fix='"hidden", a number, or [dash_mm, gap_mm].',
    )


@dataclass(frozen=True)
class VectorFrame:
    """One vector block's stated coordinate system.

    It exists so that the mm-per-unit, the drawing scale and the y
    direction are applied in exactly ONE place. Every primitive below
    calls `point` and `length` and knows nothing else about geometry -
    which is why a 100 mm line at 1:1 measures 100 mm and a 100 mm line at
    1:2 measures 50, with no per-primitive arithmetic to get wrong.
    """

    units: str
    origin: str
    unit_mm: float
    scale: float
    scale_text: str
    at_mm: tuple[float, float]
    page_h_mm: float

    @property
    def y_up(self) -> bool:
        return self.origin == "bottom_left"

    def point(self, xy: tuple[float, float]) -> tuple[float, float]:
        """A block coordinate -> fpdf page millimetres (origin top-left)."""
        x = self.at_mm[0] + xy[0] * self.unit_mm * self.scale
        y = self.at_mm[1] + xy[1] * self.unit_mm * self.scale
        return x, (self.page_h_mm - y) if self.y_up else y

    def length(self, value: float) -> float:
        """A block length (a radius, a width) -> page millimetres."""
        return float(value) * self.unit_mm * self.scale

    def summary(self) -> dict[str, Any]:
        return {
            "units": self.units,
            "origin": self.origin,
            "scale": self.scale_text,
            "at_mm": [round(self.at_mm[0], 4), round(self.at_mm[1], 4)],
        }


def _vector_frame(block: dict[str, Any], index: int, page_h_mm: float) -> VectorFrame:
    units = str(block.get("units") or "mm").strip().lower()
    if units not in VECTOR_UNITS_MM:
        raise TeeError(
            "pdf_bad_units",
            f"block {index}: '{units}' is not a unit.",
            fix=f"Use one of: {', '.join(VECTOR_UNITS_MM)}. State it - a sheet "
            "whose units are guessed is a sheet that lies.",
        )
    origin = str(block.get("origin") or "top_left").strip().lower()
    if origin not in VECTOR_ORIGINS:
        raise TeeError(
            "pdf_bad_origin",
            f"block {index}: '{origin}' is not an origin.",
            fix='Use "top_left" (PDF\'s own, y downwards) or "bottom_left" '
            "(the CAD convention, y upwards).",
        )
    scale, scale_text = _scale_factor(block.get("scale"))
    unit_mm = VECTOR_UNITS_MM[units]
    at = block.get("at") or [0, 0]
    ax, ay = _xy(at, index, "at")
    return VectorFrame(
        units=units,
        origin=origin,
        unit_mm=unit_mm,
        scale=scale,
        scale_text=scale_text,
        at_mm=(ax * unit_mm, ay * unit_mm),
        page_h_mm=page_h_mm,
    )


def _finite(value: float, code: str, what: str, fix: str) -> float:
    """NaN and infinity are not PDF numbers, and nothing downstream notices.

    MEASURED 2026-09-04: fpdf2 writes whatever float it is handed straight into
    the content stream, so `{"from": [nan, 0]}` produced `nan 28.35 m ... S` -
    a page no reader can parse - and compose still answered `ok: true`. Every
    number that reaches the stream passes through here instead (hard rule 6).
    """
    if not math.isfinite(value):
        raise TeeError(code, f"{what} is {value}, which a PDF cannot carry.", fix=fix)
    return value


def _xy(value: Any, index: int, what: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise TeeError(
            "pdf_bad_point",
            f"block {index}: '{what}' is {value!r}, not a point.",
            fix="A point is [x, y].",
        )
    try:
        x, y = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise TeeError(
            "pdf_bad_point",
            f"block {index}: '{what}' = {list(value)!r} is not two numbers.",
            fix="A point is [x, y], both numbers.",
        ) from exc
    fix = "A point is [x, y], both finite numbers."
    return (
        _finite(x, "pdf_bad_point", f"block {index}: '{what}' x", fix),
        _finite(y, "pdf_bad_point", f"block {index}: '{what}' y", fix),
    )


def _points(value: Any, index: int, what: str, minimum: int) -> list[tuple[float, float]]:
    if not isinstance(value, (list, tuple)) or len(value) < minimum:
        raise TeeError(
            "pdf_bad_vector",
            f"block {index}: '{what}' needs at least {minimum} points.",
            fix=f'"{what}": [[0, 0], [100, 0]]',
        )
    return [_xy(p, index, f"{what}[{n}]") for n, p in enumerate(value)]


def _rgb(value: Any) -> tuple[int, int, int]:
    """[r, g, b] or "#rrggbb" -> a byte triple."""
    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        try:
            return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]
        except ValueError as exc:
            raise TeeError(
                "pdf_bad_color", f"{value!r} is not a colour.", fix='Use "#rrggbb".'
            ) from exc
    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            return tuple(max(0, min(int(c), 255)) for c in value)  # type: ignore[return-value]
        except (TypeError, ValueError) as exc:
            raise TeeError(
                "pdf_bad_color", f"{list(value)!r} is not a colour.", fix="Use [r, g, b]."
            ) from exc
    raise TeeError(
        "pdf_bad_color",
        f"{value!r} is not a colour.",
        fix='Use [r, g, b] or "#rrggbb".',
    )


def _arrowhead(doc, tip: tuple[float, float], back: tuple[float, float], size_mm: float) -> None:
    """A filled triangle at `tip`, pointing away from `back`.

    Dimension lines are the reason the vector block exists at all, and an
    arrowhead is the one piece of a dimension a caller cannot assemble
    cheaply from lines - so it is one key on a line, not three items.
    """
    dx, dy = tip[0] - back[0], tip[1] - back[1]
    length = math.hypot(dx, dy)
    if length <= 1e-9 or size_mm <= 0:
        return
    ux, uy = dx / length, dy / length
    base = (tip[0] - ux * size_mm, tip[1] - uy * size_mm)
    half = size_mm * 0.28
    left = (base[0] - uy * half, base[1] + ux * half)
    right = (base[0] + uy * half, base[1] - ux * half)
    doc.polygon([tip, left, right], style="F")


def _draw_vector(doc, block: dict[str, Any], index: int, family: str, text_fn) -> tuple[int, dict]:
    """One vector block. Returns (items drawn, the frame it was drawn in)."""
    frame = _vector_frame(block, index, doc.h)
    items = block.get("items")
    if not isinstance(items, list) or not items:
        raise TeeError(
            "pdf_bad_vector",
            f"block {index}: a vector block needs a non-empty 'items' list.",
            fix=f'items: [{{"kind": "line", "from": [0, 0], "to": [100, 0]}}]. '
            f"Kinds: {', '.join(VECTOR_ITEM_KINDS)}.",
        )

    saved_width = doc.line_width
    base_width = _finite(
        float(block.get("width_mm") or DEFAULT_LINE_MM),
        "pdf_bad_vector",
        f"block {index}: 'width_mm'",
        'Pass "width_mm": 0.35 (paper millimetres).',
    )
    base_color = _rgb(block.get("color")) if block.get("color") else (0, 0, 0)
    base_dash = _dash_mm(block.get("dash"))
    base_size = _finite(
        float(block.get("size_pt") or DEFAULT_TEXT_PT),
        "pdf_bad_vector",
        f"block {index}: 'size_pt'",
        'Pass "size_pt": 8.',
    )
    drawn = 0

    for n, item in enumerate(items):
        if not isinstance(item, dict):
            raise TeeError(
                "pdf_bad_vector",
                f"block {index} item {n} is not an object.",
                fix='Each item is a dict with a "kind".',
            )
        kind = str(item.get("kind") or "").strip().lower()
        if kind not in VECTOR_ITEM_KINDS:
            raise TeeError(
                "pdf_bad_vector",
                f"block {index} item {n}: '{kind or '(missing)'}' is not a vector item.",
                fix=f"Use one of: {', '.join(VECTOR_ITEM_KINDS)}.",
            )
        width = _finite(
            float(item.get("width_mm") or base_width),
            "pdf_bad_vector",
            f"block {index} item {n}: 'width_mm'",
            'Pass "width_mm": 0.35 (paper millimetres).',
        )
        color = _rgb(item["color"]) if item.get("color") else base_color
        dash = _dash_mm(item["dash"]) if "dash" in item else base_dash
        doc.set_line_width(width)
        doc.set_draw_color(*color)
        doc.set_dash_pattern(dash=dash[0], gap=dash[1])
        fill = _rgb(item["fill"]) if item.get("fill") else None
        if fill:
            doc.set_fill_color(*fill)
        style = "DF" if fill else "D"

        if kind == "line":
            a = frame.point(_xy(item.get("from"), index, "from"))
            b = frame.point(_xy(item.get("to"), index, "to"))
            doc.line(a[0], a[1], b[0], b[1])
            arrows = str(item.get("arrows") or "none").strip().lower()
            if arrows not in ("none", "start", "end", "both"):
                raise TeeError(
                    "pdf_bad_vector",
                    f"block {index} item {n}: '{arrows}' is not an arrow setting.",
                    fix='Use "none", "start", "end" or "both".',
                )
            if arrows != "none":
                size = _finite(
                    float(item.get("arrow_mm") or DEFAULT_ARROW_MM),
                    "pdf_bad_vector",
                    f"block {index} item {n}: 'arrow_mm'",
                    'Pass "arrow_mm": 3 (paper millimetres).',
                )
                doc.set_fill_color(*color)
                if arrows in ("end", "both"):
                    _arrowhead(doc, b, a, size)
                if arrows in ("start", "both"):
                    _arrowhead(doc, a, b, size)
                if fill:
                    doc.set_fill_color(*fill)
        elif kind in ("polyline", "path"):
            pts = [frame.point(p) for p in _points(item.get("points"), index, "points", 2)]
            if kind == "path":
                if fill is None:
                    doc.set_fill_color(*color)
                doc.polygon(pts, style="DF" if item.get("stroke") else "F")
            elif item.get("close"):
                doc.polygon(pts, style=style)
            else:
                doc.polyline(pts, style=style)
        elif kind == "rect":
            ax, ay = _xy(item.get("at"), index, "at")
            w_local, h_local = _xy(item.get("size"), index, "size")
            corner = frame.point((ax, ay + h_local)) if frame.y_up else frame.point((ax, ay))
            doc.rect(
                corner[0],
                corner[1],
                frame.length(w_local),
                frame.length(h_local),
                style=style,
            )
        elif kind == "circle":
            centre = frame.point(_xy(item.get("center"), index, "center"))
            radius = frame.length(_number(item, "radius", index, n))
            # MEASURED, 2026-09-04, fpdf2 2.8.8: `circle` takes the CENTRE
            # and `arc` takes the upper-left of the bounding box, even
            # though `circle`'s own docstring still says "upper-left
            # bounding box" - it was changed in fpdf2 2.8.1 and the prose
            # was not. Probed both, hence the asymmetry below.
            doc.circle(centre[0], centre[1], radius, style=style)
        elif kind == "arc":
            centre = frame.point(_xy(item.get("center"), index, "center"))
            radius = frame.length(_number(item, "radius", index, n))
            start = _finite(
                float(item.get("start_deg") or 0.0),
                "pdf_bad_vector",
                f"block {index} item {n}: 'start_deg'",
                'Pass "start_deg": 0 (degrees).',
            )
            end = _finite(
                float(item.get("end_deg", 360.0)),
                "pdf_bad_vector",
                f"block {index} item {n}: 'end_deg'",
                'Pass "end_deg": 90 (degrees).',
            )
            # fpdf measures its arc angles in ITS frame, where y grows
            # downwards; a bottom_left block measures them in a y-up frame,
            # so the sweep mirrors. Same arc, traversed the other way.
            lo, hi = (-end, -start) if frame.y_up else (start, end)
            doc.arc(
                centre[0] - radius,
                centre[1] - radius,
                2 * radius,
                lo,
                hi,
                b=2 * radius,
                style=style,
            )
        elif kind == "text":
            _draw_vector_text(doc, item, index, n, frame, family, text_fn, base_size, color)
        drawn += 1

    doc.set_dash_pattern()
    doc.set_line_width(saved_width)
    doc.set_draw_color(0, 0, 0)
    doc.set_fill_color(0, 0, 0)
    doc.set_text_color(0, 0, 0)
    return drawn, frame.summary()


def _number(item: dict[str, Any], key: str, index: int, n: int) -> float:
    try:
        value = float(item[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise TeeError(
            "pdf_bad_vector",
            f"block {index} item {n}: '{key}' is missing or not a number.",
            fix=f'Pass "{key}": 12.5.',
        ) from exc
    return _finite(
        value, "pdf_bad_vector", f"block {index} item {n}: '{key}'", f'Pass "{key}": 12.5.'
    )


def _draw_vector_text(
    doc,
    item: dict[str, Any],
    index: int,
    n: int,
    frame: VectorFrame,
    family: str,
    text_fn,
    base_size: float,
    color: tuple[int, int, int],
) -> None:
    """Text at a point and an angle - the half of a sheet that is words."""
    anchor = frame.point(_xy(item.get("at"), index, "at"))
    body = text_fn(str(item.get("text") or ""))
    size_pt = _finite(
        float(item.get("size_pt") or base_size),
        "pdf_bad_vector",
        f"block {index} item {n}: 'size_pt'",
        'Pass "size_pt": 8.',
    )
    bold = bool(item.get("bold")) and family == "Helvetica"
    doc.set_font(family, "B" if bold else "", size_pt)
    doc.set_text_color(*color)
    width_mm = doc.get_string_width(body)
    height_mm = size_pt * 25.4 / 72.0
    align = str(item.get("align") or "left").strip().lower()
    if align not in ("left", "center", "right"):
        raise TeeError(
            "pdf_bad_vector",
            f"block {index} item {n}: '{align}' is not an alignment.",
            fix='Use "left", "center" or "right".',
        )
    valign = str(item.get("valign") or "baseline").strip().lower()
    if valign not in ("baseline", "middle", "top"):
        raise TeeError(
            "pdf_bad_vector",
            f"block {index} item {n}: '{valign}' is not a vertical alignment.",
            fix='Use "baseline" (the default), "middle" or "top".',
        )
    dx = {"left": 0.0, "center": -width_mm / 2.0, "right": -width_mm}[align]
    dy = {"baseline": 0.0, "middle": height_mm * 0.35, "top": height_mm * 0.72}[valign]
    angle = _finite(
        float(item.get("angle_deg") or 0.0),
        "pdf_bad_vector",
        f"block {index} item {n}: 'angle_deg'",
        'Pass "angle_deg": 90 (degrees, CCW in the block\'s frame).',
    )
    # A block angle is counter-clockwise in the BLOCK's frame; fpdf rotates
    # counter-clockwise on the paper. Those agree only when y points up.
    paper_angle = angle if frame.y_up else -angle
    if paper_angle % 360.0:
        with doc.rotation(paper_angle, x=anchor[0], y=anchor[1]):
            doc.text(anchor[0] + dx, anchor[1] + dy, body)
    else:
        doc.text(anchor[0] + dx, anchor[1] + dy, body)


def compose(spec: dict[str, Any]) -> dict[str, Any]:
    """Block list -> a new PDF. Returns a summary; never the file."""
    FPDF = _need_fpdf()
    out = _out_path(spec)
    blocks = spec.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise TeeError(
            "pdf_no_blocks",
            "compose needs a non-empty 'blocks' list.",
            fix=f"Kinds: {', '.join(BLOCK_KINDS)}.",
        )

    page_w, page_h = _page_mm(spec)
    doc = FPDF(format=(page_w, page_h), unit="mm")
    doc.set_auto_page_break(auto=True, margin=MARGIN_MM)
    doc.set_margins(MARGIN_MM, MARGIN_MM, MARGIN_MM)
    # A66: the flowing blocks were written against a hardcoded A4 width.
    # `doc.epw` is that same 180 mm on A4 and the RIGHT number on an A3
    # sheet, so a page size is now a parameter rather than an assumption.
    content_w = doc.epw

    # A51 P4. With a font: full Unicode. Without: Latin-1, and the
    # typographic characters it lacks are transliterated with the answer
    # saying so, rather than raising on a smart quote.
    font_spec = str(spec.get("font") or "").strip()
    family = "Helvetica"
    degraded: list[str] = []
    if font_spec:
        font_path = resolve_font(font_spec)
        doc.add_font("body", "", str(font_path))
        family = "body"

    def _text(value: str) -> str:
        if family != "Helvetica":
            return value
        safe, changed = _degrade(value)
        degraded.extend(changed)
        return safe

    title = str(spec.get("title") or "").strip()
    if title:
        doc.set_title(title)
    # A51 P5: the metadata a real document carries. Absent keys are simply
    # not set, so nothing appears that the caller did not ask for.
    for key, setter in (
        ("author", doc.set_author),
        ("subject", doc.set_subject),
        ("keywords", doc.set_keywords),
        ("creator", doc.set_creator),
    ):
        value = str(spec.get(key) or "").strip()
        if value:
            setter(value)

    # Page numbers, as a footer. fpdf2 calls `footer()` on every page break,
    # so this has to be installed BEFORE the first add_page.
    if spec.get("page_numbers"):
        footer_family = family

        def _footer():
            doc.set_y(-12)
            doc.set_font(footer_family, "", 8)
            doc.set_text_color(120, 120, 120)
            doc.cell(0, 8, f"{doc.page_no()}", align="C")
            doc.set_text_color(0, 0, 0)

        doc.footer = _footer  # type: ignore[method-assign]
    doc.add_page()
    rendered = 0
    vector_items = 0
    vector_frames: list[dict[str, Any]] = []

    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise TeeError(
                "pdf_bad_block", f"block {index} is not an object.", fix="Each block is a dict."
            )
        kind = str(block.get("kind") or "").lower()
        if kind not in BLOCK_KINDS:
            raise TeeError(
                "pdf_bad_block",
                f"block {index}: '{kind or '(missing)'}' is not a block kind.",
                fix=f"Use one of: {', '.join(BLOCK_KINDS)}.",
            )
        if kind == "page_break":
            doc.add_page()
        elif kind == "spacer":
            doc.ln(float(block.get("mm") or 4))
        elif kind == "heading":
            level = max(1, min(int(block.get("level") or 1), 3))
            heading = _text(str(block.get("text") or ""))
            # A bookmark per heading: a long report becomes navigable in any
            # viewer's outline pane, which is most of what "high end" means.
            if spec.get("outline", True):
                doc.start_section(heading, level=level - 1)
            doc.set_font(family, "B" if family == "Helvetica" else "", HEADING_SIZES[level])
            _colour(doc, block.get("color"))
            doc.multi_cell(doc.epw, HEADING_SIZES[level] * 0.5, heading)
            doc.set_text_color(0, 0, 0)
            doc.ln(2)
        elif kind == "paragraph":
            doc.set_font(family, "", 11)
            _colour(doc, block.get("color"))
            doc.multi_cell(doc.epw, 5.5, _text(str(block.get("text") or "")))
            doc.set_text_color(0, 0, 0)
            doc.ln(2)
        elif kind == "image":
            raw = str(block.get("path") or "").strip()
            img_path = Path(raw).expanduser()
            if not img_path.is_file():
                raise TeeError(
                    "pdf_missing_image",
                    f"block {index}: no such image {img_path}",
                    fix="Pass a path that exists.",
                )
            width = float(block.get("width_mm") or content_w)
            width = max(10.0, min(width, content_w))
            doc.image(_jpeg_bytes(img_path), w=width)
            caption = str(block.get("caption") or "").strip()
            if caption:
                doc.set_font(family, "I" if family == "Helvetica" else "", 9)
                doc.multi_cell(doc.epw, 4.5, _text(caption))
            doc.ln(3)
        elif kind == "table":
            rows = block.get("rows")
            if not isinstance(rows, list) or not rows:
                raise TeeError(
                    "pdf_bad_block",
                    f"block {index}: a table needs a non-empty 'rows' list.",
                    fix='rows: [["Part", "Qty"], ["Leg", "4"]]',
                )
            columns = max(len(r) for r in rows)
            col_w = content_w / columns
            for r_index, row in enumerate(rows):
                header = bool(block.get("header")) and r_index == 0
                doc.set_font(family, ("B" if header else "") if family == "Helvetica" else "", 10)
                shade = header and block.get("shade_header", True)
                if shade:
                    doc.set_fill_color(232, 232, 236)
                for cell in list(row) + [""] * (columns - len(row)):
                    doc.cell(col_w, 6, _text(str(cell)), border=1, fill=bool(shade))
                doc.ln(6)
            doc.ln(2)
        elif kind == "vector":
            count, frame = _draw_vector(doc, block, index, family, _text)
            vector_items += count
            vector_frames.append(frame)
        rendered += 1

    doc.output(str(out))
    size = out.stat().st_size
    result: dict[str, Any] = {
        "ok": True,
        "path": str(out),
        "pages": doc.pages_count if hasattr(doc, "pages_count") else len(doc.pages),
        "bytes": size,
        "blocks_rendered": rendered,
        "page_mm": [round(page_w, 4), round(page_h, 4)],
        "note": "A summary, not the document. Read it back with ex_ingest / "
        "tee_media, or open the path.",
    }
    if vector_frames:
        # The frames are echoed because a drawing that does not say its own
        # scale is a drawing nobody can build from. This is the answer's
        # half of that contract.
        result["vector_items"] = vector_items
        result["vector_frames"] = vector_frames
    if family != "Helvetica":
        result["font"] = str(resolve_font(font_spec))
    if degraded:
        unique = sorted(set(degraded))
        result["degraded_characters"] = unique
        result["degraded_count"] = len(degraded)
        result["degraded_note"] = (
            f"{len(degraded)} character(s) were transliterated to Latin-1 "
            f"({' '.join(unique[:8])}): the core PDF fonts cannot encode them. "
            "Meaning is preserved - a curly quote becomes a straight one - but "
            'pass font: "Arial Unicode.ttf" (or any TTF path) to keep the '
            "originals and to use Greek, CJK or symbols."
        )
    return result


def _pages_arg(spec: dict[str, Any], total: int, key: str = "pages") -> list[int]:
    """1-based page numbers from a list or 'A-B' ranges -> 0-based indices."""
    raw = spec.get(key)
    if raw in (None, "", []):
        return list(range(total))
    if isinstance(raw, str):
        wanted: list[int] = []
        for part in raw.split(","):
            part = part.strip()
            if "-" in part:
                a, _, b = part.partition("-")
                wanted.extend(range(int(a), int(b) + 1))
            elif part:
                wanted.append(int(part))
    elif isinstance(raw, list):
        wanted = [int(x) for x in raw]
    else:
        raise TeeError(
            "pdf_bad_pages", f"'{key}' must be a list or a range string.", fix='e.g. "1-3,7"'
        )
    out = []
    for n in wanted:
        if not 1 <= n <= total:
            raise TeeError(
                "pdf_bad_pages",
                f"page {n} is outside this document (1-{total}).",
                fix="Pages are 1-based.",
            )
        out.append(n - 1)
    return out


def _stamp_overlay(text: str, image: str, page_w: float, page_h: float, spec: dict[str, Any]):
    """A single-page PDF holding just the mark, sized to the target page."""
    FPDF = _need_fpdf()
    doc = FPDF(unit="pt", format=(page_w, page_h))
    doc.set_auto_page_break(auto=False)
    doc.add_page()
    x = float(spec.get("x") or page_w * 0.18)
    y = float(spec.get("y") or page_h * 0.45)
    if image:
        img_path = Path(image).expanduser()
        if not img_path.is_file():
            raise TeeError(
                "pdf_missing_image", f"no such stamp image {img_path}", fix="Pass a real path."
            )
        doc.image(_jpeg_bytes(img_path), x=x, y=y, w=float(spec.get("width_pt") or page_w * 0.3))
    if text:
        doc.set_font("Helvetica", "B", int(spec.get("size_pt") or 48))
        grey = int(spec.get("grey") or 200)
        doc.set_text_color(grey, grey, grey)
        with doc.rotation(float(spec.get("rotate_deg") or 30), x=x, y=y):
            doc.text(x, y, text)
    buf = io.BytesIO(doc.output())
    buf.seek(0)
    return buf


def edit(spec: dict[str, Any]) -> dict[str, Any]:
    """Page surgery and overlays. In -> out, never in place."""
    pypdf = _need_pypdf()
    op = str(spec.get("op") or "").lower()
    if op not in EDIT_OPS:
        raise TeeError(
            "pdf_bad_op",
            f"'{op or '(missing)'}' is not an edit operation.",
            fix=f"Use one of: {', '.join(EDIT_OPS)}. Rewriting the TEXT inside "
            "an existing PDF is deliberately not offered - a PDF stores "
            "positioned glyph runs, not paragraphs, so re-flowing them "
            "corrupts the layout silently. Use 'stamp' to add a mark, or "
            "pdf_compose to build a new document.",
        )

    inputs_raw = spec.get("inputs") or ([spec["input"]] if spec.get("input") else [])
    if not inputs_raw:
        raise TeeError(
            "pdf_no_input",
            "edit needs 'input' (or 'inputs' for merge).",
            fix='Pass {"input": "a.pdf"}.',
        )
    inputs = [Path(str(p)).expanduser() for p in inputs_raw]
    for path in inputs:
        if not path.is_file():
            raise TeeError("pdf_missing_input", f"No such PDF: {path}", fix="Check the path.")

    writer = pypdf.PdfWriter()
    detail: dict[str, Any] = {}

    if op == "merge":
        if len(inputs) < 2:
            raise TeeError(
                "pdf_no_input",
                "merge needs at least two inputs.",
                fix='"inputs": ["a.pdf", "b.pdf"]',
            )
        for path in inputs:
            for page in pypdf.PdfReader(str(path)).pages:
                writer.add_page(page)
        detail["merged"] = [p.name for p in inputs]
    else:
        reader = pypdf.PdfReader(str(inputs[0]))
        total = len(reader.pages)
        detail["source_pages"] = total
        if op == "split":
            out_dir = Path(str(spec.get("out_dir") or inputs[0].parent)).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            written = []
            for index in _pages_arg(spec, total):
                one = pypdf.PdfWriter()
                one.add_page(reader.pages[index])
                target = out_dir / f"{inputs[0].stem}_p{index + 1}.pdf"
                if target.exists() and not spec.get("overwrite"):
                    raise TeeError(
                        "pdf_exists", f"{target} already exists.", fix="Pass overwrite: true."
                    )
                with target.open("wb") as fh:
                    one.write(fh)
                written.append(str(target))
            return {
                "ok": True,
                "op": op,
                "files": written,
                "pages_each": 1,
                "note": "A summary, not the documents.",
            }
        if op in ("reorder", "extract_pages"):
            for index in _pages_arg(spec, total):
                writer.add_page(reader.pages[index])
        elif op == "delete_pages":
            drop = set(_pages_arg(spec, total))
            if not drop:
                raise TeeError(
                    "pdf_bad_pages", "delete_pages needs pages to delete.", fix='"pages": [2]'
                )
            for index, page in enumerate(reader.pages):
                if index not in drop:
                    writer.add_page(page)
            detail["deleted"] = sorted(n + 1 for n in drop)
        elif op == "rotate":
            degrees = int(spec.get("degrees") or 90)
            if degrees % 90:
                raise TeeError(
                    "pdf_bad_rotation",
                    f"{degrees} is not a multiple of 90.",
                    fix="PDF rotation is quarter turns: 90, 180, 270.",
                )
            targets = set(_pages_arg(spec, total))
            for index, page in enumerate(reader.pages):
                writer.add_page(page.rotate(degrees) if index in targets else page)
            detail["rotated"] = degrees
        elif op == "stamp":
            text = str(spec.get("text") or "").strip()
            image = str(spec.get("image") or "").strip()
            if not text and not image:
                raise TeeError(
                    "pdf_nothing_to_stamp",
                    "stamp needs 'text' or 'image'.",
                    fix='e.g. {"op": "stamp", "text": "DRAFT"}',
                )
            targets = set(_pages_arg(spec, total))
            for index, page in enumerate(reader.pages):
                if index in targets:
                    box = page.mediabox
                    overlay = pypdf.PdfReader(
                        _stamp_overlay(text, image, float(box.width), float(box.height), spec)
                    ).pages[0]
                    page.merge_page(overlay)
                writer.add_page(page)
            detail["stamped_pages"] = sorted(n + 1 for n in targets)

    out = _out_path(spec)
    with out.open("wb") as fh:
        writer.write(fh)
    return {
        "ok": True,
        "op": op,
        "path": str(out),
        "pages": len(writer.pages),
        "bytes": out.stat().st_size,
        **detail,
        "note": "A summary, not the document. The input was not modified.",
    }


def register_pdf_tools(app, project_root: str | Path) -> None:
    """Register pdf_* as virtual tools (the surface stays 17)."""
    from tee.kernel.registry import VirtualTool

    app.registry.register(
        VirtualTool(
            name="pdf_compose",
            description=(
                "WRITE a new PDF from a block list: headings, paragraphs, "
                "tables, images (HEIC included, no conversion needed), page "
                "breaks, and `vector` blocks of lines, polylines, "
                "rectangles, circles, arcs, filled paths and text placed at "
                "an exact point and angle - enough for a technical sheet: "
                "visible and hidden (dashed) edges, dimension lines with "
                "arrowheads, a title block. A vector block STATES its "
                "coordinate system (units, origin, scale, insertion point) "
                "and the answer echoes it back. Any page size, portrait or "
                "landscape. Plus metadata, page numbers, bookmarks and "
                "per-block colour. Pass `font` (a TTF path or system font "
                "name) for full Unicode - Greek, CJK, symbols; without it "
                "text is Latin-1 and curly quotes are transliterated with a "
                "note rather than failing. Returns a summary - path, pages, "
                "bytes - never the document itself."
            ),
            schema={
                "type": "object",
                "properties": {
                    "out": {"type": "string", "description": "Destination path."},
                    "title": {"type": "string"},
                    "page": {
                        "description": 'Page size: "A4" (default), "A3", "A0".."A5", '
                        '"letter", "legal", "tabloid" - or [width_mm, height_mm].',
                    },
                    "orientation": {
                        "type": "string",
                        "enum": ["portrait", "landscape"],
                        "description": "Swaps whatever size you named. Default portrait.",
                    },
                    "font": {
                        "type": "string",
                        "description": "A .ttf/.otf path or a system font name "
                        "(e.g. 'Arial Unicode.ttf'). Without one, text is Latin-1 "
                        "and curly quotes are transliterated with a note.",
                    },
                    "author": {"type": "string"},
                    "subject": {"type": "string"},
                    "keywords": {"type": "string"},
                    "page_numbers": {"type": "boolean"},
                    "outline": {
                        "type": "boolean",
                        "description": "Headings become PDF bookmarks. Default true.",
                    },
                    "overwrite": {"type": "boolean"},
                    "blocks": {
                        "type": "array",
                        "description": "heading{text,level} | paragraph{text} | "
                        "image{path,caption,width_mm} | table{rows,header} | "
                        "page_break | spacer{mm} | vector{units,origin,scale,at,items}. "
                        "A vector block draws in a STATED frame: units mm|cm|in|pt, "
                        'origin top_left|bottom_left, scale "1:2" or 0.5, '
                        "at [x,y] = where its (0,0) sits on the paper (unscaled). "
                        "Items: line{from,to,arrows} | polyline{points,close} | "
                        "rect{at,size} | circle{center,radius} | "
                        "arc{center,radius,start_deg,end_deg} | path{points,fill} | "
                        "text{at,text,size_pt,angle_deg,align,valign}. Styling is in "
                        "PAPER units and never scaled: width_mm, dash "
                        '("hidden"|[dash_mm,gap_mm]), color, fill, size_pt.',
                        "items": {"type": "object"},
                    },
                },
                "required": ["out", "blocks"],
            },
            handler=lambda args: compose(args),
            tags=[
                "pdf",
                "write",
                "compose",
                "report",
                "document",
                "create pdf",
                "generate pdf",
                "export",
                "paperwork",
            ],
            examples=[
                {
                    "out": "docs/site-note.pdf",
                    "blocks": [
                        {"kind": "heading", "text": "Site note", "level": 1},
                        {"kind": "paragraph", "text": "Gable G3 is unplastered."},
                    ],
                },
                {
                    "out": "docs/bracket.pdf",
                    "page": "A3",
                    "orientation": "landscape",
                    "blocks": [
                        {
                            "kind": "vector",
                            "units": "mm",
                            "origin": "bottom_left",
                            "scale": "1:2",
                            "at": [40, 40],
                            "items": [
                                {"kind": "rect", "at": [0, 0], "size": [120, 80]},
                                {
                                    "kind": "line",
                                    "from": [0, -12],
                                    "to": [120, -12],
                                    "arrows": "both",
                                },
                                {
                                    "kind": "text",
                                    "at": [60, -10],
                                    "text": "120",
                                    "align": "center",
                                },
                            ],
                        }
                    ],
                },
            ],
        )
    )

    app.registry.register(
        VirtualTool(
            name="pdf_edit",
            description=(
                "EDIT an existing PDF by page: merge, split, reorder, "
                "rotate, delete_pages, extract_pages, or stamp a watermark "
                "or image onto chosen pages. Reads the input and writes a "
                "NEW file - the input is never modified. Rewriting the text "
                "inside a PDF is not offered: a PDF stores positioned glyph "
                "runs, not paragraphs, so re-flowing them corrupts the "
                "layout silently. Use stamp, or pdf_compose for a new doc."
            ),
            schema={
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": list(EDIT_OPS)},
                    "input": {"type": "string"},
                    "inputs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "merge only.",
                    },
                    "out": {"type": "string"},
                    "out_dir": {"type": "string", "description": "split only."},
                    "pages": {"description": '[1,3] or "1-3,7"; 1-based. Default: all.'},
                    "degrees": {"type": "integer", "description": "rotate only, multiple of 90."},
                    "text": {"type": "string", "description": "stamp only."},
                    "image": {"type": "string", "description": "stamp only."},
                    "overwrite": {"type": "boolean"},
                },
                "required": ["op", "out"],
            },
            handler=lambda args: edit(args),
            tags=[
                "pdf",
                "edit",
                "merge",
                "split",
                "rotate",
                "watermark",
                "stamp",
                "pages",
                "combine pdf",
                "delete page",
            ],
            examples=[{"op": "stamp", "input": "report.pdf", "out": "draft.pdf", "text": "DRAFT"}],
        )
    )
