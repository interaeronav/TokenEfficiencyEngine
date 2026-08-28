"""HTML -> inert budgeted quote (research 49, mitigation 1).

A dumb stdlib parser on purpose: script/style/template/noscript/head,
comments, and hidden elements (hidden attr, display:none,
visibility:hidden, zero-size) never reach the text; zero-width and
bidi-control characters are dropped; whitespace is normalized; a hard cap
bounds the worst page. What remains is the page's visible words - quoted
data, never instructions - cut to a token budget with a simple
question-overlap score so the quote spends its budget near the answer.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError

MAX_TEXT_CHARS = 400_000  # hard cap before budgeting (~115K tokens)
DEFAULT_MAX_TOKENS = 500

_SKIP_TAGS = {"script", "style", "template", "noscript", "head", "iframe", "svg"}
_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}  # fmt: skip
_BLOCK_TAGS = {
    "p", "div", "section", "article", "li", "tr", "br", "nav", "header",
    "footer", "table", "ul", "ol", "blockquote", "pre", "h1", "h2", "h3",
    "h4", "h5", "h6", "dt", "dd", "figcaption", "summary",
}  # fmt: skip
_HIDDEN_STYLE = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?![.\d])"
    r"|(?:^|;)\s*width\s*:\s*0(?:px)?\s*(?:;|$)|(?:^|;)\s*height\s*:\s*0(?:px)?\s*(?:;|$)",
    re.IGNORECASE,
)
# Zero-width + bidi control characters (injection camouflage) - dropped.
_DROP_CHARS = dict.fromkeys(map(ord, "​‌‍⁠﻿­‪‫‬‭‮⁦⁧⁨⁩"))
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_WORD = re.compile(r"[a-z0-9_().]+")
_STOPWORDS = frozenset(
    [
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "to",
        "of",
        "in",
        "on",
        "at",
        "and",
        "or",
        "for",
        "with",
        "how",
        "what",
        "when",
        "where",
        "which",
        "why",
        "who",
        "whom",
        "must",
        "should",
        "could",
        "would",
        "can",
        "may",
        "does",
        "do",
        "did",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "from",
        "as",
        "by",
        "not",
        "no",
        "if",
        "then",
        "than",
        "into",
        "about",
    ]
)


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def _is_hidden(self, attrs: list[tuple[str, str | None]]) -> bool:
        for name, value in attrs:
            if name == "hidden":
                return True
            if name == "style" and value and _HIDDEN_STYLE.search(value):
                return True
        return False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._skip_depth:
            if tag not in _VOID_TAGS:
                self._skip_depth += 1
            return
        if tag in _SKIP_TAGS or (tag not in _VOID_TAGS and self._is_hidden(attrs)):
            self._skip_depth = 1
            return
        if tag == "img":  # alt text is visible-page content: data, kept
            alt = dict(attrs).get("alt")
            if alt:
                self.parts.append(f"\n{alt}\n")
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._skip_depth:
            self.handle_starttag(tag, attrs)  # void: starttag never opens a skip

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            if tag not in _VOID_TAGS:
                self._skip_depth -= 1
            return
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data:
            # Whitespace runs inside a text node are just whitespace;
            # paragraph breaks come only from block tags.
            self.parts.append(re.sub(r"\s+", " ", data))

    def handle_comment(self, data: str) -> None:  # comments are a hidden channel
        return


def extract_text(html: str) -> str:
    """Visible page text: sanitized, normalized, hard-capped."""
    parser = _TextParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass  # whatever was parsed before the failure is what we quote
    raw = "".join(parser.parts).translate(_DROP_CHARS)
    lines = [" ".join(line.split()) for line in raw.split("\n")]
    text = "\n".join(line for line in lines if line)
    return text[:MAX_TEXT_CHARS]


def page_title(html: str) -> str | None:
    match = _TITLE.search(html[:65536])
    if not match:
        return None
    title = " ".join(match.group(1).split()).translate(_DROP_CHARS)
    return title or None


def _question_words(question: str) -> set[str]:
    words = set(_WORD.findall(question.lower()))
    return {w.strip(".") for w in words if w.strip(".") not in _STOPWORDS and len(w) > 2}


def focus_extract(text: str, question: str, max_tokens: int) -> tuple[str, bool]:
    """Cut text to the budget, spending it on question-relevant paragraphs
    first (document order preserved). Returns (quote, truncated)."""
    if estimate_tokens(text) <= max_tokens:
        return text, False
    paragraphs = [p for p in text.split("\n") if p.strip()]
    qwords = _question_words(question)

    def score(paragraph: str) -> int:
        words = {w.strip(".") for w in _WORD.findall(paragraph.lower())}
        return len(qwords & words)

    ranked = sorted(range(len(paragraphs)), key=lambda i: (-score(paragraphs[i]), i))
    chosen: list[int] = []
    seen: set[str] = set()
    used = 0
    for index in ranked:
        # a verbatim repeat (boilerplate, nav, promo blocks) adds nothing to
        # a quote and crowds distinct content out of the budget (A35 P3.2)
        normalized = " ".join(paragraphs[index].split()).lower()
        if normalized in seen:
            continue
        cost = estimate_tokens(paragraphs[index]) + 1
        if used + cost > max_tokens:
            continue
        chosen.append(index)
        seen.add(normalized)
        used += cost
    if not chosen:  # a single paragraph bigger than the whole budget
        head = paragraphs[0][: int(max_tokens * 3.2)]
        return head, True
    quote = "\n".join(paragraphs[i] for i in sorted(chosen))
    return quote, True


def build_answer(
    html: str,
    question: str,
    *,
    url: str,
    retrieved_at: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    title: str | None = None,
) -> dict:
    """The web_lookup answer contract: {quote, source, retrieved_at, truncated}."""
    text = extract_text(html)
    if not text.strip():
        raise TeeError(
            "web_no_text",
            "The page has no extractable text (empty, script-only, or non-HTML).",
            fix="JS-only apps and binary files have no text path; try a "
            "documentation URL, or the media lane for images/PDF.",
        )
    quote, truncated = focus_extract(text, question, max_tokens)
    return {
        "ok": True,
        "quote": quote,
        "source": {"url": url, "title": title or page_title(html)},
        "retrieved_at": retrieved_at,
        "truncated": truncated,
    }
