"""web_lookup's PDF arm (A53 P0a).

The defect this replaces: an `application/pdf` URL was decoded as UTF-8 and
handed to the HTML extractor, so the answer quoted the file's own header
bytes back at the caller - `%PDF-1.7 %...  3085 0 obj` - while
`web/extract.py` told the caller to use "the media lane for images/PDF", a
route that did not exist. Every test here asserts the same law: a PDF
answers as prose or refuses by name, and never as bytes.
"""

from __future__ import annotations

import sys

import pytest
from fixtures_web import HOSTILE_BODY

from tee.kernel.errors import TeeError
from tee.web import media as web_media
from tee.web.fetch import WebFetcher
from tee.web.tools import WebLookupService

pytest.importorskip("fpdf", reason="[pdf] extra builds the fixture PDFs")
pytest.importorskip("pypdf", reason="[pdf] extra reads them back")

URL = "http://docs.example/fabric-properties.pdf"
SENTENCE = "Bending rigidity is measured in warp, weft and bias directions."


def _pdf_bytes(*, text: str | None) -> bytes:
    """A real PDF. `text=None` builds one with no text layer at all - the
    scanned-page case, which must refuse rather than answer with nothing."""
    from fpdf import FPDF

    doc = FPDF()
    doc.add_page()
    if text is None:
        doc.rect(20, 20, 60, 40)
    else:
        doc.set_font("helvetica", size=12)
        doc.set_title("Fabric properties for virtual simulation")
        doc.multi_cell(0, 8, text)
    return bytes(doc.output())


def service(tmp_path, body: bytes, *, url: str = URL) -> WebLookupService:
    routes = {
        "http://docs.example/robots.txt": (404, {}, b""),
        url: (200, {"Content-Type": "application/pdf"}, body),
    }
    fetcher = WebFetcher(
        tmp_path,
        transport=lambda target, headers, timeout: routes[target.url],
        resolve=lambda host, port: ["93.184.216.34"],
        min_interval_s=0.0,
        sleep=lambda s: None,
    )
    return WebLookupService(tmp_path, fetcher=fetcher)


def test_pdf_answers_with_prose_not_bytes(tmp_path) -> None:
    svc = service(tmp_path, _pdf_bytes(text=SENTENCE))
    answer = svc.lookup(URL, "which directions is bending measured in?")

    assert answer["ok"] is True
    assert "warp" in answer["quote"]
    assert "%PDF" not in answer["quote"]  # the defect, named
    assert "obj" not in answer["quote"].split()  # ...and its neighbours
    assert answer["media"] == {"kind": "pdf", "pages": 1, "extractor": "pypdf"}
    assert answer["source"]["url"] == URL
    assert answer["source"]["title"] == "Fabric properties for virtual simulation"


def test_scanned_pdf_refuses_by_name_with_the_route_that_works(tmp_path) -> None:
    svc = service(tmp_path, _pdf_bytes(text=None))
    with pytest.raises(TeeError) as excinfo:
        svc.lookup(URL, "what does it say?")
    assert excinfo.value.code == "web_pdf_no_text"
    assert "ex_add" in excinfo.value.fix  # names the lane that CAN read a scan


def test_missing_extra_refuses_with_the_install_command(tmp_path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "pypdf", None)  # import pypdf -> ImportError
    svc = service(tmp_path, _pdf_bytes(text=SENTENCE))
    with pytest.raises(TeeError) as excinfo:
        svc.lookup(URL, "what does it say?")
    assert excinfo.value.code == "web_pdf_unavailable"
    assert "tee-engine[pdf]" in excinfo.value.fix


def test_malformed_pdf_refuses_rather_than_quoting_rubble(tmp_path) -> None:
    svc = service(tmp_path, b"%PDF-1.7\nnot actually a pdf at all\n")
    with pytest.raises(TeeError) as excinfo:
        svc.lookup(URL, "what does it say?")
    assert excinfo.value.code in {"web_pdf_unreadable", "web_pdf_no_text"}


def test_detection_is_magic_bytes_not_the_url(tmp_path) -> None:
    assert web_media.looks_pdf(b"%PDF-1.7\n...") is True
    assert web_media.looks_pdf(b"\xef\xbb\xbf\n  %PDF-1.4") is True  # BOM + space
    assert web_media.looks_pdf(HOSTILE_BODY.encode()) is False
    assert web_media.looks_pdf(b"") is False

    # A page that merely LIVES at a .pdf URL but serves HTML still reads as HTML.
    svc = service(tmp_path, HOSTILE_BODY.encode())
    answer = svc.lookup(URL, "how thick is bedding sand?")
    assert "25 to 40 mm" in answer["quote"]
    assert "media" not in answer
