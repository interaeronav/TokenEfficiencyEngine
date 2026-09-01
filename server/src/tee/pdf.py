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
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

BLOCK_KINDS = ("heading", "paragraph", "image", "table", "page_break", "spacer")
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
    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        rgb = tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
    elif isinstance(value, (list, tuple)) and len(value) == 3:
        rgb = tuple(max(0, min(int(c), 255)) for c in value)
    else:
        raise TeeError(
            "pdf_bad_color",
            f"{value!r} is not a colour.",
            fix='Use [r, g, b] or "#rrggbb".',
        )
    doc.set_text_color(*rgb)


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

    doc = FPDF(format="A4", unit="mm")
    doc.set_auto_page_break(auto=True, margin=MARGIN_MM)
    doc.set_margins(MARGIN_MM, MARGIN_MM, MARGIN_MM)

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
            width = float(block.get("width_mm") or CONTENT_W_MM)
            width = max(10.0, min(width, CONTENT_W_MM))
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
            col_w = CONTENT_W_MM / columns
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
        rendered += 1

    doc.output(str(out))
    size = out.stat().st_size
    result: dict[str, Any] = {
        "ok": True,
        "path": str(out),
        "pages": doc.pages_count if hasattr(doc, "pages_count") else len(doc.pages),
        "bytes": size,
        "blocks_rendered": rendered,
        "note": "A summary, not the document. Read it back with ex_ingest / "
        "tee_media, or open the path.",
    }
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
                "tables, images (HEIC included, no conversion needed) and "
                "page breaks, plus metadata, page numbers, bookmarks and "
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
                        "page_break | spacer{mm}",
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
                }
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
