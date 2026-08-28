"""Extractor + answer-contract spec for the web lane (A34 W0).

Research 49, mitigation 1: fetched content is data, never instructions.
Hidden channels (script/style/template/comment/hidden/zero-size) are
stripped; visible channels pass through as inert quoted material inside a
fixed answer schema; zero-width and bidi controls are dropped; everything
is budgeted. The extractor is a pure function - same input, same output,
no I/O.
"""

from __future__ import annotations

import pytest
from fixtures_web import (
    DOCS_PAGE,
    HOSTILE_ALT,
    HOSTILE_BODY,
    HOSTILE_HIDDEN,
    HOSTILE_UNICODE,
    INJECTION,
    TINY_PAGE,
)

from tee.kernel.budget import estimate_tokens
from tee.web import extract

RETRIEVED = "2026-08-28T12:00:00Z"


# --- sanitizer: hidden channels stripped, visible channels inert ------------


def test_hidden_channels_are_stripped() -> None:
    text = extract.extract_text(HOSTILE_HIDDEN)
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" not in text
    assert "Non-manifold edges" in text
    assert "Fill holes before exporting" in text


def test_visible_body_injection_passes_through_as_data() -> None:
    # Visible page text is quoted faithfully - dropping it would misreport
    # the page; the schema and description label it untrusted instead.
    text = extract.extract_text(HOSTILE_BODY)
    assert INJECTION in text
    assert "Bedding sand" in text


def test_alt_text_passes_through_as_data() -> None:
    text = extract.extract_text(HOSTILE_ALT)
    assert INJECTION in text
    assert "Corrugated iron" in text


def test_zero_width_and_bidi_controls_dropped() -> None:
    text = extract.extract_text(HOSTILE_UNICODE)
    assert "IGNORE" in text  # the zero-width space inside "IG​NORE" is gone
    for ch in ("​", "⁠", "‮", "‬", "⁦", "⁩"):
        assert ch not in text


def test_script_and_style_and_title_not_in_body_text() -> None:
    text = extract.extract_text(DOCS_PAGE)
    assert ".nav" not in text
    assert "color: red" not in text
    assert "bmesh module gives direct access" in text


def test_whitespace_normalized_and_paragraphs_kept() -> None:
    text = extract.extract_text("<p>a\n\n\n   b</p><p>next   para</p>")
    assert "a b" in text
    assert "next para" in text
    assert "  " not in text.replace("\n", " ")


def test_extractor_is_pure() -> None:
    assert extract.extract_text(HOSTILE_BODY) == extract.extract_text(HOSTILE_BODY)


def test_giant_input_is_capped_not_fatal() -> None:
    page = "<body>" + ("<p>word</p>" * 400_000)
    text = extract.extract_text(page)
    assert len(text) <= extract.MAX_TEXT_CHARS


def test_title_extracted() -> None:
    assert extract.page_title(DOCS_PAGE) == "bmesh module reference"
    assert extract.page_title("<body>no title</body>") is None


# --- question-focused budget cut --------------------------------------------


def test_focus_prefers_question_relevant_paragraphs() -> None:
    text = extract.extract_text(DOCS_PAGE)
    quote, truncated = extract.focus_extract(text, "when must free() be called on a bmesh?", 120)
    assert "free()" in quote
    assert truncated is True
    assert "Filler paragraph 180" not in quote


def test_focus_respects_budget() -> None:
    text = extract.extract_text(DOCS_PAGE)
    for budget in (120, 500):
        quote, _ = extract.focus_extract(text, "boolean manifold", budget)
        assert estimate_tokens(quote) <= budget + 20  # paragraph-boundary slack


def test_small_page_untruncated() -> None:
    text = extract.extract_text(TINY_PAGE)
    quote, truncated = extract.focus_extract(text, "anything at all", 500)
    assert truncated is False
    assert "One short paragraph" in quote


# --- the answer schema ------------------------------------------------------


def test_answer_schema_shape() -> None:
    answer = extract.build_answer(
        HOSTILE_BODY, "how thick is bedding sand?", url="https://ex.com/p", retrieved_at=RETRIEVED
    )
    assert answer["ok"] is True
    assert set(answer) >= {"ok", "quote", "source", "retrieved_at", "truncated"}
    assert answer["source"] == {"url": "https://ex.com/p", "title": "Paving guide"}
    assert answer["retrieved_at"] == RETRIEVED
    assert isinstance(answer["truncated"], bool)
    assert "25 to 40 mm" in answer["quote"]


def test_answer_quote_is_budgeted() -> None:
    answer = extract.build_answer(
        DOCS_PAGE, "boolean", url="https://ex.com/d", retrieved_at=RETRIEVED, max_tokens=200
    )
    assert estimate_tokens(answer["quote"]) <= 220
    assert answer["truncated"] is True


# --- the tool description contract ------------------------------------------


def test_tool_description_states_untrusted_content() -> None:
    from tee.web.tools import WEB_LOOKUP_DESCRIPTION

    lowered = WEB_LOOKUP_DESCRIPTION.lower()
    assert "untrusted" in lowered
    assert "never instructions" in lowered


def test_empty_page_answers_loud() -> None:
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as excinfo:
        extract.build_answer(
            "<html><body><script>x</script></body></html>",
            "anything",
            url="https://ex.com/e",
            retrieved_at=RETRIEVED,
        )
    assert excinfo.value.code == "web_no_text"
    assert excinfo.value.fix


def test_focus_extract_dedups_verbatim_repeats():
    """Repeated boilerplate must not crowd distinct content out of the
    budget: a paragraph is quoted once, and the freed budget buys the
    lower-scoring but distinct paragraph (A35 P3.2)."""
    from tee.web.extract import focus_extract

    promo = "Concrete pavers bed on thirty mm of sharp sand over compacted hardcore."
    distinct = "Joint the pavers with kiln-dried sand brushed in dry."
    filler = "x " * 2400  # forces the budget cut path
    text = "\n".join([promo, promo, promo, distinct, filler])
    quote, truncated = focus_extract(text, "how do pavers bed on sand", max_tokens=60)
    assert truncated
    assert quote.count(promo) == 1
    assert distinct in quote
