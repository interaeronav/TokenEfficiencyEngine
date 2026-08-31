# CLAUDE_A48_SCRIPT.md — finish the senses, then teach TEE to write PDFs

**Owner directives (2026-08-31, verbatim):** *"add in a feature that allows
users to write and edit pdfs"* — and finish what remains of A47
(`CLAUDE_A47_SCRIPT.md` P5). Written to be executed by a fresh Opus
session with no memory of this one.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, work in `server/`. Branch
  `claude/token-efficiency-engine-5jv1dj` ONLY. Read `docs/PROGRESS.md`
  first; update it with real command output after every phase; commit and
  push per finished item (imperative subject, body explains why).
- Suite: `uv run pytest -q -m "not dcc"` from `server/`. Expect ~1,118
  passing. `uv run ruff check .` must stay clean. The always-loaded
  surface must stay **17 tools**, measured at **2,034 tok** on the wire
  (`uv run --project server python benchmarks/run_benchmarks.py` from the
  repo root, `surface:` line); budget ±10 around 2,028.
- **The upgrade trap:** installing any new `.mcpb` wipes the fleet extras
  from the Desktop venv. After every install:
  `uv pip install --python "<extension venv>/bin/python"
  'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]'
  'tee-engine[extract]'` — then re-run `extras.remember` happens at next
  boot on its own. TEE detects and names the loss since 0.13.0.
- Local model shim on `127.0.0.1:4000` (LiteLLM). Vision =
  `claude-qwen-vl` (17 GB, lazy-started, EVICTS the 86 GB DeepSeek; ~10 s
  reload on the next text turn; cold start ~36 s measured). Blender bridge
  usually live on port 9876 (the chair scene).
- Downloads over 2 GB: ask the owner first. This binds the P0 audition.

## What exists (verified 2026-08-31, do not rebuild)

- `tee/senses.py`: `sense_describe`, `sense_transcribe`, `sense_viewport`,
  `sense_camera` — all live, tested, portable via `[senses]` config.
- PDF **read** is done: `extract/documents.py` (pdfplumber + pypdfium2,
  dimension parsing, scale ladder, OCR) and `tee_media` renders pages.
- PDF **write** exists only as a dev-group habit: `fpdf2>=2.8.8` sits in
  `[dependency-groups] dev` and deliverable PDFs (the AURA-X chair set)
  were built inline with no kept script — the exact pre-P3c pattern the
  pipeline lane was built to end.
- No edit machinery at all: `pypdf`/`pikepdf` absent from the tree.

## Laws (inherited A46/A47, plus PDF-specific)

1. Measured before/after; nothing claimed working that was not run.
2. Surface invariant: 17 tools; `pdf_*` are VIRTUAL tools.
3. **Never a silent overwrite.** `out` is required and explicit; an
   existing file refuses unless `overwrite: true`. Inputs are never
   written to — an edit reads A and writes B.
4. **Answers are summaries, never payloads.** A compose returns
   `{path, pages, bytes}`; nobody gets a PDF inline.
5. Licences recorded in DECISIONS.md before adoption: fpdf2 is
   **LGPL-3.0** and pypdf is **BSD-3** — fine for the owner's private,
   non-distributed use (the pillow-heif precedent); re-examine if TEE is
   ever distributed.
6. Trust: table `pdf_compose`/`pdf_edit` EXPLICITLY (never a family
   prefix) on `write-artifacts`. Verify the grant exists at the owner's
   root before claiming the lane usable there.

## P0 — close A47 P5 (carried, do first)

1. Move the image-QA scenario into `benchmarks/` (one question about one
   4K site frame): seeing host via `tee_media` (budgeted 756 host tokens,
   10,764 full) vs blind host via `sense_describe` (~65 host tokens).
   Record in `benchmarks/RESULTS.md`: **11.6x vs budgeted, 165x vs full**
   — these replace the earlier informal "33x", which measured
   provider-side tokens, not what a host pays. State that correction.
2. Re-measure the text↔vision alternation cost THROUGH `sense_describe`
   (not the raw shim) and record whether `COLD_START_S = 6.0` in
   `senses.py` matches observation; adjust from measurement only.
3. **Small-VLM audition.** Pick ONE 2B-class vision model (≤2 GB download
   — over that, stop and ask the owner). Serve it however the shim
   allows, then run the SAME two probes the 30B passed: the unguessable
   card (`PLINTH K-4713 / CURE 21 DAYS`, fixture at scratchpad
   `probe.png` — regenerate with PIL if gone: white card, red border,
   those two lines) must read back EXACTLY; the gable-vs-spec delta
   (frame `DJI_0100_t0006s.jpg`, context "drawings say gable G3 is solid
   plastered brick") must answer the delta. Adopt as default provider
   ONLY on both passing exactly; otherwise record the failure and keep
   the 30B. Either way, record footprint arithmetic: can it coexist with
   the 86 GB DeepSeek (128 GB machine)?
4. Ship 0.15.0 (bundle + verify from clean unzip over MCP stdio: 17
   tools, version line), extras-restore note in the release text.

## P1 — `pdf_compose` (write)

New `tee/pdf.py` + `[pdf]` extra = `fpdf2` (move it out of the dev group;
dev keeps it via the extra). Spec → new PDF:

```
{"out": "docs/report.pdf",
 "title": "...",                      # optional metadata
 "blocks": [
   {"kind": "heading", "text": "...", "level": 1},
   {"kind": "paragraph", "text": "..."},
   {"kind": "image", "path": "site/frame.jpg", "caption": "...",
    "width_mm": 160},
   {"kind": "table", "rows": [[...], [...]], "header": true},
   {"kind": "page_break"}]}
```

Images load through `tee.kernel.imaging.open_image` so **HEIC embeds with
no conversion** (the v0.11.0 door; re-encode to JPEG in-memory for fpdf2).
Return `{ok, path, pages, bytes, blocks_rendered}`. Refusals: missing
`out`, existing file without `overwrite`, unknown block kind (name the
kinds), image path absent.
*Acceptance:* compose a 2-page PDF containing a heading, a paragraph, a
table and one HEIC image; **read it back with the EXISTING extract lane**
(pdfplumber) and assert the text round-trips; suite green.

## P2 — `pdf_edit` (page surgery + overlay)

Add `pypdf` (BSD-3) to the `[pdf]` extra. One tool, `op`-dispatched, in →
out, never in-place:

- `merge` (inputs list), `split` (page ranges → files), `reorder`,
  `rotate`, `delete_pages`, `extract_pages`
- `stamp`: overlay text or an image at a position on chosen pages
  (compose the overlay page with fpdf2, `merge_page` with pypdf) — this
  is how "editing" text lands in v1: additive, honest.

**Refuse true in-place text rewriting, and say why in the refusal:** PDF
text is layout-fragmented spans; silently re-flowing it corrupts
documents. That is v2 work if ever, not a silent failure.
*Acceptance:* merge two composed PDFs, delete a page, stamp a draft
watermark; every output read back via pdfplumber and page counts
asserted; a `sense_describe` on a `pypdfium2`-rendered page confirms the
stamp is VISIBLE (the senses lane checking the pdf lane — dogfood).

## P3 — surface and ship

- Tool descriptions carry the token story (summaries out, never the file
  inline). `tee_search_tools "write a pdf" / "edit pdf pages"` must rank
  the new tools top-3.
- DECISIONS.md licence entry; docs page `docs/pdf-lane.md` with the spec
  shape and the in-place-rewrite refusal rationale.
- Suite, benchmarks surface line within budget, version 0.16.0, bundle,
  clean-unzip MCP verify, extras note. PROGRESS throughout.

## Out of scope

AcroForm filling, signatures, encryption, OCR (exists in extract), true
text reflow editing, and any PDF rendering service. The senses lane and
pipeline lane are done — do not reopen them beyond P0's carried items.
