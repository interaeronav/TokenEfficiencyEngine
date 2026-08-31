# The PDF lane — `pdf_compose` and `pdf_edit` (A48)

TEE could already **read** a PDF well: `extract/documents.py` pulls text,
dimension strings and a scale ladder out of one, and `tee_media` renders a
page. It could not write one. `fpdf2` sat in the dev dependency group and
the AURA-X chair deliverables were built by running it inline with no
script kept — the exact pattern the pipeline lane exists to end.

Install: `uv pip install 'tee-engine[pdf]'` (fpdf2 + pypdf).

## `pdf_compose` — write a new document

```json
{"out": "docs/site-note.pdf",
 "title": "Okongo site note",
 "blocks": [
   {"kind": "heading",   "text": "Okongo site note", "level": 1},
   {"kind": "paragraph", "text": "Gable G3 was specified as solid plastered brick."},
   {"kind": "table", "header": true,
    "rows": [["Element", "Spec", "As-built"],
             ["Gable G3", "plastered", "exposed brick"]]},
   {"kind": "page_break"},
   {"kind": "image", "path": "site/IMG_2984.HEIC",
    "caption": "Straight off the phone.", "width_mm": 150}]}
```

Kinds: `heading` (level 1–3), `paragraph`, `image`, `table`, `page_break`,
`spacer`. **HEIC images embed with no conversion** — they open through the
same door added in v0.11.0 and are handed to fpdf2 as JPEG in memory.

Returns a summary — `{path, pages, bytes, blocks_rendered}` — never the
document. A PDF in a model's context is a token catastrophe and answers no
question; read it back with `ex_ingest`/`tee_media` if you need to see it.

## `pdf_edit` — page surgery and overlays

`merge`, `split`, `reorder`, `rotate`, `delete_pages`, `extract_pages`,
`stamp`. Pages are **1-based**, given as `[1, 3]` or `"1-3,7"`.

```json
{"op": "stamp", "input": "report.pdf", "out": "draft.pdf", "text": "DRAFT"}
```

Every operation **reads A and writes B**. The input is never modified, and
`out` is required — TEE does not choose filenames, and an existing file
refuses unless you pass `overwrite: true`. Silently replacing a document
someone made is not a default.

## What this will not do, and why

**Rewriting the text inside an existing PDF is refused by name.**

A PDF does not store paragraphs. It stores positioned glyph runs — often
split mid-word across several show-text operators — with line breaks,
kerning and column widths baked in when the file was made. "Change this
sentence" means re-flowing spans whose geometry was decided by a layout
engine that is no longer present. The failure mode is not a crash; it is a
document that opens perfectly and is subtly wrong: overlapping text, lost
line breaks, a table whose columns no longer line up.

Tools that offer this usually mean "cover the old text with a white box and
draw new text on top", which is a stamp with a misleading name. So the lane
offers the honest version:

- **`stamp`** to add a mark, a watermark or an image over existing pages;
- **`pdf_compose`** to build a corrected document from content you control.

The refusal says all of this in its `fix`, so a model that tries gets the
reason and the two real options rather than a dead end.

## Verified by TEE's own eye

`stamp` writes text that pdfplumber cannot extract — it is drawn, rotated,
in an overlay. So the acceptance test renders the page with `pypdfium2` and
asks `sense_describe`:

> *"Is there a large diagonal watermark word across this page?"*
> *"Yes, there is a large diagonal watermark word across this page. The word
> is 'DRAFT'."*

The senses lane checking the PDF lane — which is the only way to confirm a
visual mark actually landed.
