"""A48 — writing and editing PDFs, and the edit that is refused.

TEE could read a PDF well and not write one: `fpdf2` sat in the dev
dependency group and the AURA-X chair deliverables were built by running it
inline with no script kept - the pre-pipeline-lane pattern. These tests pin
the lane and, more importantly, the two places it says no.
"""

from __future__ import annotations

import pytest

from tee import pdf
from tee.kernel.errors import TeeError

pdfplumber = pytest.importorskip("pdfplumber")
pytest.importorskip("fpdf")
pytest.importorskip("pypdf")


def _doc(tmp_path, name="a.pdf", blocks=None):
    return pdf.compose(
        {
            "out": str(tmp_path / name),
            "blocks": blocks
            or [
                {"kind": "heading", "text": "Okongo site note", "level": 1},
                {"kind": "paragraph", "text": "Gable G3 is unplastered."},
            ],
        }
    )


# -- compose ----------------------------------------------------------------


def test_composed_text_round_trips_through_the_existing_reader(tmp_path):
    """The acceptance that matters: TEE's PDF must be readable by TEE's own
    extract lane, not merely openable."""
    _doc(tmp_path)
    with pdfplumber.open(tmp_path / "a.pdf") as doc:
        text = "\n".join((p.extract_text() or "") for p in doc.pages)
    assert "Okongo site note" in text and "Gable G3 is unplastered." in text


def test_a_page_break_makes_a_page_and_a_table_survives(tmp_path):
    pdf.compose(
        {
            "out": str(tmp_path / "t.pdf"),
            "blocks": [
                {
                    "kind": "table",
                    "header": True,
                    "rows": [["Element", "Spec"], ["Gable G3", "plastered"]],
                },
                {"kind": "page_break"},
                {"kind": "paragraph", "text": "Second page."},
            ],
        }
    )
    with pdfplumber.open(tmp_path / "t.pdf") as doc:
        assert len(doc.pages) == 2
        first = doc.pages[0].extract_text() or ""
    assert "Element" in first and "plastered" in first


def test_the_answer_is_a_summary_never_the_document(tmp_path):
    r = _doc(tmp_path)
    assert set(r) >= {"ok", "path", "pages", "bytes", "blocks_rendered"}
    assert not any(isinstance(v, (bytes, bytearray)) for v in r.values())
    assert "summary, not the document" in r["note"]


def test_an_existing_file_is_never_silently_replaced(tmp_path):
    _doc(tmp_path)
    with pytest.raises(TeeError) as e:
        _doc(tmp_path)
    assert e.value.code == "pdf_exists"
    assert "overwrite: true" in e.value.fix
    _doc(tmp_path, blocks=[{"kind": "paragraph", "text": "replaced"}]) if False else None
    r = pdf.compose(
        {
            "out": str(tmp_path / "a.pdf"),
            "overwrite": True,
            "blocks": [{"kind": "paragraph", "text": "replaced on purpose"}],
        }
    )
    assert r["ok"]


def test_out_is_required_because_tee_does_not_pick_paths(tmp_path):
    with pytest.raises(TeeError) as e:
        pdf.compose({"blocks": [{"kind": "paragraph", "text": "x"}]})
    assert e.value.code == "pdf_no_out"


def test_an_unknown_block_kind_names_the_kinds(tmp_path):
    with pytest.raises(TeeError) as e:
        pdf.compose({"out": str(tmp_path / "x.pdf"), "blocks": [{"kind": "video"}]})
    assert "heading" in e.value.fix and "table" in e.value.fix


def test_a_missing_image_refuses_before_writing_anything(tmp_path):
    out = tmp_path / "x.pdf"
    with pytest.raises(TeeError) as e:
        pdf.compose({"out": str(out), "blocks": [{"kind": "image", "path": "/nope.jpg"}]})
    assert e.value.code == "pdf_missing_image"
    assert not out.exists(), "a refused compose left a partial file"


# -- edit -------------------------------------------------------------------


def test_merge_then_delete_then_stamp(tmp_path):
    _doc(tmp_path, "a.pdf")
    _doc(tmp_path, "b.pdf", [{"kind": "paragraph", "text": "Appendix B."}])
    m = pdf.edit(
        {
            "op": "merge",
            "inputs": [str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf")],
            "out": str(tmp_path / "m.pdf"),
        }
    )
    assert m["pages"] == 2
    d = pdf.edit(
        {
            "op": "delete_pages",
            "input": str(tmp_path / "m.pdf"),
            "pages": [2],
            "out": str(tmp_path / "d.pdf"),
        }
    )
    assert d["pages"] == 1 and d["deleted"] == [2]
    s = pdf.edit(
        {
            "op": "stamp",
            "input": str(tmp_path / "d.pdf"),
            "text": "DRAFT",
            "out": str(tmp_path / "s.pdf"),
        }
    )
    assert s["stamped_pages"] == [1]
    with pdfplumber.open(tmp_path / "s.pdf") as doc:
        assert len(doc.pages) == 1


def test_the_input_is_never_modified(tmp_path):
    _doc(tmp_path, "a.pdf")
    before = (tmp_path / "a.pdf").read_bytes()
    pdf.edit(
        {
            "op": "rotate",
            "input": str(tmp_path / "a.pdf"),
            "degrees": 90,
            "out": str(tmp_path / "r.pdf"),
        }
    )
    assert (tmp_path / "a.pdf").read_bytes() == before


def test_rewriting_text_is_refused_with_the_reason(tmp_path):
    """The important refusal. A PDF stores positioned glyph runs, not
    paragraphs; re-flowing them corrupts layout silently, which is worse
    than declining."""
    _doc(tmp_path, "a.pdf")
    with pytest.raises(TeeError) as e:
        pdf.edit(
            {"op": "replace_text", "input": str(tmp_path / "a.pdf"), "out": str(tmp_path / "x.pdf")}
        )
    assert e.value.code == "pdf_bad_op"
    assert "positioned glyph runs" in e.value.fix
    assert "stamp" in e.value.fix and "pdf_compose" in e.value.fix


def test_a_quarter_turn_is_the_only_rotation_a_pdf_has(tmp_path):
    _doc(tmp_path, "a.pdf")
    with pytest.raises(TeeError) as e:
        pdf.edit(
            {
                "op": "rotate",
                "input": str(tmp_path / "a.pdf"),
                "degrees": 45,
                "out": str(tmp_path / "x.pdf"),
            }
        )
    assert "quarter turns" in e.value.fix


def test_pages_outside_the_document_refuse_by_number(tmp_path):
    _doc(tmp_path, "a.pdf")
    with pytest.raises(TeeError) as e:
        pdf.edit(
            {
                "op": "delete_pages",
                "input": str(tmp_path / "a.pdf"),
                "pages": [9],
                "out": str(tmp_path / "x.pdf"),
            }
        )
    assert "1-1" in e.value.message and "1-based" in e.value.fix


def test_split_writes_one_file_per_page(tmp_path):
    pdf.compose(
        {
            "out": str(tmp_path / "two.pdf"),
            "blocks": [
                {"kind": "paragraph", "text": "one"},
                {"kind": "page_break"},
                {"kind": "paragraph", "text": "two"},
            ],
        }
    )
    r = pdf.edit(
        {
            "op": "split",
            "input": str(tmp_path / "two.pdf"),
            "out": str(tmp_path / "ignored.pdf"),
            "out_dir": str(tmp_path / "parts"),
        }
    )
    assert len(r["files"]) == 2


# -- registration -----------------------------------------------------------


def test_both_tools_write_artifacts_and_are_explicitly_tabled():
    from tee.kernel import trust

    assert trust.capability_for("pdf_compose") == "write-artifacts"
    assert trust.capability_for("pdf_edit") == "write-artifacts"
    assert "pdf_compose" in trust._EXPLICIT


def test_the_tools_are_discoverable_by_plain_language(tmp_path):
    from tee.app import TeeApp
    from tee.pdf import register_pdf_tools

    app = TeeApp({}, project_root=tmp_path)
    register_pdf_tools(app, tmp_path)
    for query, expected in (
        ("write a pdf report", "pdf_compose"),
        ("edit pdf pages", "pdf_edit"),
        ("add a watermark to a document", "pdf_edit"),
    ):
        top = [i["name"] for i in app.registry.search(query)["items"]][:3]
        assert expected in top, f"{query!r} -> {top}"


# -- A51 P4: ordinary prose stopped being fatal -----------------------------


def test_a_smart_quote_no_longer_destroys_a_report(tmp_path):
    """The live bug. The core PDF fonts are Latin-1, so curly quotes and em
    dashes did not degrade - they RAISED, and one of them killed a whole
    compose. They appear in almost any text a model writes."""
    r = pdf.compose(
        {
            "out": str(tmp_path / "q.pdf"),
            "blocks": [
                {"kind": "paragraph", "text": "The gable was “solid plastered brick” — it is not."}
            ],
        }
    )
    assert r["ok"]
    assert set(r["degraded_characters"]) == {"“", "”", "—"}
    assert "Meaning is preserved" in r["degraded_note"]
    assert "font" in r["degraded_note"], "the note must name the way to keep the originals"


def test_transliteration_preserves_meaning_and_is_never_silent(tmp_path):
    from tee.pdf import _degrade

    text, changed = _degrade("“as-built” — the owner’s note…")  # noqa: RUF001 - the ambiguous glyph IS the test
    assert text == '"as-built" - the owner\'s note...'
    assert changed  # and compose reports these; silence is the failure mode


def test_latin1_characters_are_left_alone(tmp_path):
    """façade and m² are already encodable - transliterating them would be
    damage, not rescue."""
    from tee.pdf import _degrade

    text, changed = _degrade("façade Ångström 3.5 m² 45° ±2")
    assert text == "façade Ångström 3.5 m² 45° ±2"
    assert changed == []


@pytest.mark.skipif(
    not __import__("pathlib")
    .Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    .is_file(),
    reason="no system Unicode font",
)
def test_an_embedded_font_keeps_everything(tmp_path):
    out = tmp_path / "u.pdf"
    r = pdf.compose(
        {
            "out": str(out),
            "font": "Arial Unicode.ttf",
            "blocks": [{"kind": "paragraph", "text": "“as-built” — 3.5 m², α β, 建築"}],  # noqa: RUF001 - the ambiguous glyph IS the test
        }
    )
    assert "degraded_characters" not in r
    with pdfplumber.open(out) as doc:
        text = doc.pages[0].extract_text() or ""
    for probe in ("as-built", "m²", "α", "建築"):  # noqa: RUF001 - the ambiguous glyph IS the test
        assert probe in text, f"{probe!r} did not survive"


def test_a_font_is_resolved_by_name_or_refused_with_where_to_look():
    from tee.pdf import resolve_font

    with pytest.raises(TeeError) as e:
        resolve_font("NoSuchFontAnywhere.ttf")
    assert e.value.code == "pdf_font_missing"
    assert "/System/Library/Fonts" in e.value.fix


# -- A51 P5: the attributes a real document carries -------------------------


def test_metadata_lands(tmp_path):
    out = tmp_path / "m.pdf"
    pdf.compose(
        {
            "out": str(out),
            "title": "T",
            "author": "A",
            "subject": "S",
            "keywords": "k1, k2",
            "blocks": [{"kind": "paragraph", "text": "body"}],
        }
    )
    with pdfplumber.open(out) as doc:
        md = doc.metadata
    assert md.get("Title") == "T" and md.get("Author") == "A"
    assert md.get("Subject") == "S"


def test_headings_become_bookmarks(tmp_path):
    import pypdf

    out = tmp_path / "b.pdf"
    pdf.compose(
        {
            "out": str(out),
            "blocks": [
                {"kind": "heading", "text": "One", "level": 1},
                {"kind": "paragraph", "text": "x"},
                {"kind": "heading", "text": "Two", "level": 1},
            ],
        }
    )
    assert len(pypdf.PdfReader(str(out)).outline) == 2


def test_page_numbers_are_opt_in(tmp_path):
    plain = tmp_path / "p.pdf"
    numbered = tmp_path / "n.pdf"
    blocks = [{"kind": "paragraph", "text": "body"}]
    pdf.compose({"out": str(plain), "blocks": blocks})
    pdf.compose({"out": str(numbered), "blocks": blocks, "page_numbers": True})
    with pdfplumber.open(numbered) as doc:
        assert "1" in (doc.pages[0].extract_text() or "")
    with pdfplumber.open(plain) as doc:
        assert (doc.pages[0].extract_text() or "").strip() == "body"


def test_a_bad_colour_refuses_with_the_two_forms(tmp_path):
    with pytest.raises(TeeError) as e:
        pdf.compose(
            {
                "out": str(tmp_path / "c.pdf"),
                "blocks": [{"kind": "heading", "text": "h", "color": "octarine"}],
            }
        )
    assert e.value.code == "pdf_bad_color"
    assert "#rrggbb" in e.value.fix
