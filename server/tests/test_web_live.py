"""Live reproduction of the research-49 measurements (A34 W2 acceptance).

The three pages measured on 2026-08-28 (raw 54K-345K tokens each) must
come back as ~500-token budgeted, cited extracts through the real guarded
fetcher. Network-marked: excluded from the hermetic suite, run with
`-m network`.
"""

from __future__ import annotations

import pytest

from tee.kernel.budget import estimate_tokens
from tee.web.extract import build_answer
from tee.web.fetch import WebFetcher

PAGES = [
    (
        "https://docs.blender.org/api/current/bmesh.html",
        "when must free() be called on a bmesh?",
    ),
    (
        "https://en.wikipedia.org/wiki/Block_paving",
        "how thick should the bedding sand layer be?",
    ),
    (
        "https://pypi.org/project/trimesh/",
        "what does trimesh do and what are its core dependencies?",
    ),
]


@pytest.mark.network
@pytest.mark.timeout(180)
@pytest.mark.parametrize(("url", "question"), PAGES)
def test_research49_pages_reproduce_500_token_extracts(tmp_path, network, url, question) -> None:
    fetcher = WebFetcher(tmp_path)
    result = fetcher.fetch(url)
    if len(result.body) < 10_000 and b"required part of this site" in result.body:
        # PyPI intermittently answers rapid repeat hits with a ~3KB bot
        # challenge; the extractor quotes it faithfully (self-describing),
        # but it cannot reproduce the research-49 measurement this run.
        pytest.skip(f"{url} served its bot-challenge variant, not content")
    raw_tokens = estimate_tokens(result.body.decode("utf-8", errors="replace"))
    answer = build_answer(
        result.body.decode("utf-8", errors="replace"),
        question,
        url=result.url,
        retrieved_at=result.retrieved_at,
    )
    quote_tokens = estimate_tokens(answer["quote"])
    assert answer["ok"] is True
    assert answer["source"]["url"] == result.url
    assert 150 <= quote_tokens <= 520, f"{url}: {quote_tokens} tok"
    assert raw_tokens > 10 * quote_tokens, f"{url}: raw {raw_tokens} vs quote {quote_tokens}"
