"""KB retrieval: deterministic keyword scoring over the manifest index (16.2).

No embeddings, no runtime downloads - word overlap against titles, ids,
tags, summaries and the H2 heading index, with exact-match filters. An
empty result returns the domain table as the cheap next move, not silence.
"""

from __future__ import annotations

import re
from typing import Any

from tee.kb.index import KbIndex

_WORDS = re.compile(r"[a-z0-9]+")
_FIELD_WEIGHTS = (
    ("title", 3.0),
    ("id", 3.0),
    ("tags", 2.5),
    ("summary", 1.5),
    ("headings", 1.0),
)
DEFAULT_LIMIT = 8
LIMIT_CAP = 20

# -- top-match strength (SI-B10, the SI-B2 discipline) -----------------------
# The additive scorer above substring-matches every word incl. stop words, so
# an off-domain question still crowns SOME file (measured 2026-08-29: misfire
# questions scored 10.5-20.5 raw vs 5.0-15.5 for in-domain ones - raw score
# separates nothing). What DOES separate, cleanly, is whether any content
# word of the query hits an identity field (title/id/tags) at a word
# boundary: 0 for every recorded misfire, >=1 for every in-domain query.
# The notes below make that visible; consumers (the web kb_hint) suppress on
# them. Prefixes are a tested contract - web/tools.py matches them.

NOTE_NO_STRONG = (
    "no strong match (title/id/tag hits: none) - the corpus may not cover "
    "this; other words or a domain filter may help"
)
NOTE_WEAK_PREFIX = "weak match - only "

_STOP = frozenset(
    [
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "do",
        "does",
        "did",
        "done",
        "how",
        "what",
        "which",
        "when",
        "where",
        "why",
        "who",
        "whom",
        "can",
        "could",
        "should",
        "would",
        "will",
        "shall",
        "may",
        "might",
        "must",
        "i",
        "my",
        "me",
        "mine",
        "we",
        "our",
        "you",
        "your",
        "it",
        "its",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "from",
        "with",
        "without",
        "and",
        "or",
        "nor",
        "not",
        "no",
        "any",
        "this",
        "that",
        "these",
        "those",
        "have",
        "has",
        "had",
        "get",
        "gets",
        "got",
        "use",
        "used",
        "using",
        "into",
        "onto",
        "about",
        "above",
        "below",
        "than",
        "then",
        "there",
        "their",
        "they",
        "them",
        "if",
        "but",
        "by",
        "as",
        "so",
        "up",
        "down",
        "out",
        "over",
        "under",
        "more",
        "most",
        "some",
        "such",
        "only",
        "also",
        "just",
        "like",
        "need",
        "make",
        "made",
        "work",
        "works",
        "working",
        "thing",
        "things",
        "way",
        "ways",
        "one",
        "two",
        "three",
        "per",
        "via",
        "each",
        "all",
        "both",
        "same",
        "other",
        "another",
        "new",
        "old",
        "very",
        "much",
        "many",
        "few",
        "own",
        "off",
        "again",
        "once",
        "here",
        "now",
        "still",
        "yet",
    ]
)


def _content_words(query: str) -> list[str]:
    """The words that can attest relevance: 3+ chars and not stop words."""
    return [w for w in _WORDS.findall(str(query or "").lower()) if len(w) >= 3 and w not in _STOP]


def identity_hits(query: str, record: dict[str, Any]) -> list[str]:
    """Content words of the query found word-bounded in title/id/tags
    (a trailing s is tolerated both ways: wall<->walls)."""
    tags = record.get("tags") or []
    hay = " ".join(
        [str(record.get("title", "")), str(record.get("id", ""))]
        + [str(t) for t in (tags if isinstance(tags, list) else [tags])]
    ).lower()
    hit = []
    for w in _content_words(query):
        stems = [w] + ([w[:-1]] if w.endswith("s") and len(w) >= 4 else [])
        if any(re.search(rf"\b{re.escape(s)}s?\b", hay) for s in stems):
            hit.append(w)
    return hit


def _haystacks(record: dict[str, Any]) -> list[tuple[str, float]]:
    out = []
    for field, weight in _FIELD_WEIGHTS:
        value = record.get(field, "")
        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        out.append((str(value).lower(), weight))
    return out


def _passes(record: dict[str, Any], filters: dict[str, str]) -> bool:
    for key, wanted in filters.items():
        if wanted and str(record.get(key, "")).lower() != wanted.lower():
            return False
    return True


def hit_row(record: dict[str, Any]) -> dict[str, Any]:
    """A search row: identity + the corpus's own flags, verbatim."""
    row = {
        "id": record["id"],
        "title": record["title"],
        "domain": record["domain"],
        "confidence": record["confidence"],
        "jurisdiction": record["jurisdiction"],
        "summary": str(record.get("summary", ""))[:160],
    }
    if record.get("status") and record["status"] != "stable":
        row["status"] = record["status"]
    return row


def search(
    index: KbIndex,
    query: str,
    *,
    domain: str | None = None,
    jurisdiction: str | None = None,
    confidence: str | None = None,
    status: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    limit = max(1, min(int(limit or DEFAULT_LIMIT), LIMIT_CAP))
    filters = {
        "domain": domain or "",
        "jurisdiction": jurisdiction or "",
        "confidence": confidence or "",
        "status": status or "",
    }
    words = _WORDS.findall(str(query or "").lower())
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for record in index.records():
        if not _passes(record, filters):
            continue
        score = 0.0
        for word in words:
            for text, weight in _haystacks(record):
                if word in text:
                    score += weight
                    break
        if score > 0 or not words:
            scored.append((score, record["path"], record))
    scored.sort(key=lambda item: (-item[0], item[1]))
    hits = [hit_row(record) for _, _, record in scored[:limit]]
    out: dict[str, Any] = {"query": query, "items": hits, "matched": len(scored)}
    if words and hits:
        ident = identity_hits(query, scored[0][2])
        if not ident:
            out["note"] = NOTE_NO_STRONG
        elif len(ident) == 1:
            out["note"] = f"{NOTE_WEAK_PREFIX}'{ident[0]}' hits a title/id/tag"
    if not hits:
        data = index.load()
        out["hint"] = "no match - pick a domain and search inside it"
        out["domains"] = [{"slug": d["slug"], "files": d["files"]} for d in data.get("domains", [])]
    drift = index.load().get("drift", {})
    if drift.get("stale"):
        out["stale"] = drift.get("fix", "index is stale - see kb_status")
    return out
