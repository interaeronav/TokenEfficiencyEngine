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
                },  # fmt: skip
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
        }  # fmt: skip
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
    m = pdf.edit({"op": "merge", "inputs": [str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf")],
                  "out": str(tmp_path / "m.pdf")})  # fmt: skip
    assert m["pages"] == 2
    d = pdf.edit({"op": "delete_pages", "input": str(tmp_path / "m.pdf"), "pages": [2],
                  "out": str(tmp_path / "d.pdf")})  # fmt: skip
    assert d["pages"] == 1 and d["deleted"] == [2]
    s = pdf.edit({"op": "stamp", "input": str(tmp_path / "d.pdf"), "text": "DRAFT",
                  "out": str(tmp_path / "s.pdf")})  # fmt: skip
    assert s["stamped_pages"] == [1]
    with pdfplumber.open(tmp_path / "s.pdf") as doc:
        assert len(doc.pages) == 1


def test_the_input_is_never_modified(tmp_path):
    _doc(tmp_path, "a.pdf")
    before = (tmp_path / "a.pdf").read_bytes()
    pdf.edit({"op": "rotate", "input": str(tmp_path / "a.pdf"), "degrees": 90,
              "out": str(tmp_path / "r.pdf")})  # fmt: skip
    assert (tmp_path / "a.pdf").read_bytes() == before


def test_rewriting_text_is_refused_with_the_reason(tmp_path):
    """The important refusal. A PDF stores positioned glyph runs, not
    paragraphs; re-flowing them corrupts layout silently, which is worse
    than declining."""
    _doc(tmp_path, "a.pdf")
    with pytest.raises(TeeError) as e:
        pdf.edit({"op": "replace_text", "input": str(tmp_path / "a.pdf"),
                  "out": str(tmp_path / "x.pdf")})  # fmt: skip
    assert e.value.code == "pdf_bad_op"
    assert "positioned glyph runs" in e.value.fix
    assert "stamp" in e.value.fix and "pdf_compose" in e.value.fix


def test_a_quarter_turn_is_the_only_rotation_a_pdf_has(tmp_path):
    _doc(tmp_path, "a.pdf")
    with pytest.raises(TeeError) as e:
        pdf.edit({"op": "rotate", "input": str(tmp_path / "a.pdf"), "degrees": 45,
                  "out": str(tmp_path / "x.pdf")})  # fmt: skip
    assert "quarter turns" in e.value.fix


def test_pages_outside_the_document_refuse_by_number(tmp_path):
    _doc(tmp_path, "a.pdf")
    with pytest.raises(TeeError) as e:
        pdf.edit({"op": "delete_pages", "input": str(tmp_path / "a.pdf"), "pages": [9],
                  "out": str(tmp_path / "x.pdf")})  # fmt: skip
    assert "1-1" in e.value.message and "1-based" in e.value.fix


def test_split_writes_one_file_per_page(tmp_path):
    pdf.compose({"out": str(tmp_path / "two.pdf"), "blocks": [
        {"kind": "paragraph", "text": "one"}, {"kind": "page_break"},
        {"kind": "paragraph", "text": "two"}]})  # fmt: skip
    r = pdf.edit({"op": "split", "input": str(tmp_path / "two.pdf"),
                  "out": str(tmp_path / "ignored.pdf"), "out_dir": str(tmp_path / "parts")})  # fmt: skip
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
