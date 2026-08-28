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
    if not hits:
        data = index.load()
        out["hint"] = "no match - pick a domain and search inside it"
        out["domains"] = [{"slug": d["slug"], "files": d["files"]} for d in data.get("domains", [])]
    drift = index.load().get("drift", {})
    if drift.get("stale"):
        out["stale"] = drift.get("fix", "index is stale - see kb_status")
    return out
