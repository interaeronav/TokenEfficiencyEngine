"""Optional semantic ranking for asset search ([assets-embed]).

Model: **SigLIP 2** (`google/siglip2-base-patch16-224`, Apache-2.0, ungated).
Chosen over MobileCLIP deliberately - MobileCLIP's repo is MIT but its
*weights* are research-only, which makes it unusable in a tool whose whole
asset story is licence hygiene (research 25).

Scope, stated honestly: `AssetRow` carries name, tags, class and dimensions -
**no thumbnail path** - so what can be compared at search time is query text
against row text. SigLIP's text tower is trained for image-text alignment
rather than text-text similarity, so this is a hypothesis to be measured, not
an obvious win; `evaluate()` exists to check it against plain keyword ranking
on a labelled set before anyone turns it on.

Everything is lazy: importing this module costs nothing, and the model is
only loaded when a search actually asks for semantic ranking.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MODEL_ID = "google/siglip2-base-patch16-224"
MODEL_LICENSE = "Apache-2.0"


class SiglipTextEmbedder:
    """Text-side embeddings with an on-disk cache.

    The cache matters more than it looks: asset names and tags repeat across
    searches, so after the first pass almost every row is a dictionary hit and
    the model is never touched.
    """

    def __init__(self, cache_dir: Path | str | None = None, model_id: str = MODEL_ID):
        self.model_id = model_id
        self.cache_dir = Path(cache_dir).expanduser() if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._model = None
        self._tokenizer = None
        self._device = "cpu"
        self._memo: dict[str, list[float]] = {}

    # -- loading -----------------------------------------------------------

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(
                "semantic asset ranking needs the [assets-embed] extra (torch, transformers)"
            ) from exc
        from tee.assets.generation import torch_device

        self._device = torch_device()
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        model = AutoModel.from_pretrained(self.model_id)
        model.eval()
        self._model = model.to(self._device)
        self._torch = torch

    # -- embedding ---------------------------------------------------------

    def _cache_path(self, text: str) -> Path | None:
        if not self.cache_dir:
            return None
        key = hashlib.sha256(f"{self.model_id}\x00{text}".encode()).hexdigest()
        return self.cache_dir / f"{key[:2]}" / f"{key}.json"

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Unit-normalised text vectors, cached in memory and on disk."""
        out: list[list[float] | None] = [None] * len(texts)
        missing: list[tuple[int, str]] = []
        for index, text in enumerate(texts):
            if text in self._memo:
                out[index] = self._memo[text]
                continue
            path = self._cache_path(text)
            if path is not None and path.exists():
                try:
                    vector = json.loads(path.read_text())
                    self._memo[text] = vector
                    out[index] = vector
                    continue
                except (OSError, ValueError):
                    pass
            missing.append((index, text))

        if missing:
            self._ensure_model()
            torch = self._torch
            # SigLIP is trained with a fixed 64-token context and its
            # tokenizer will not pad to a common length without being told.
            batch = self._tokenizer(
                [t for _, t in missing],
                padding="max_length",
                max_length=64,
                truncation=True,
                return_tensors="pt",
            ).to(self._device)
            with torch.no_grad():
                features = self._model.get_text_features(**batch)
                # transformers 5.x returns a ModelOutput here where 4.x
                # returned a bare tensor; accept either.
                if not hasattr(features, "norm"):
                    pooled = getattr(features, "pooler_output", None)
                    features = pooled if pooled is not None else features[0]
                features = features / features.norm(dim=-1, keepdim=True)
            vectors = features.detach().cpu().tolist()
            for (index, text), vector in zip(missing, vectors, strict=True):
                self._memo[text] = vector
                out[index] = vector
                path = self._cache_path(text)
                if path is not None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with contextlib.suppress(OSError):
                        path.write_text(json.dumps(vector))
        return [v for v in out if v is not None]

    # -- ranking hook ------------------------------------------------------

    def score_rows(self, query: str, rows: list[Any]) -> dict[str, float]:
        """{row key -> 0..1 similarity}. Batched: one forward pass, not N."""
        if not query.strip() or not rows:
            return {}
        texts = [row_text(row) for row in rows]
        vectors = self.embed([query, *texts])
        if len(vectors) != len(texts) + 1:
            return {}
        query_vector, row_vectors = vectors[0], vectors[1:]
        scores: dict[str, float] = {}
        for row, vector in zip(rows, row_vectors, strict=True):
            similarity = sum(a * b for a, b in zip(query_vector, vector, strict=True))
            # cosine in [-1, 1] -> [0, 1]; SigLIP text-text similarities sit in
            # a narrow band, so the caller weights this modestly.
            scores[row_key(row)] = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
        return scores


def row_text(row: Any) -> str:
    parts = [getattr(row, "name", "") or ""]
    parts.extend(getattr(row, "tags", None) or [])
    asset_class = getattr(row, "asset_class", None)
    if asset_class:
        parts.append(asset_class)
    return " ".join(str(p) for p in parts if p).strip()


def row_key(row: Any) -> str:
    return f"{getattr(row, 'source', '?')}:{getattr(row, 'id', '?')}"


def evaluate(embedder: SiglipTextEmbedder, cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Does semantic ranking actually beat keyword ranking here?

    `cases` are {query, rows, relevant: [row_key,...]}. Returns mean
    reciprocal rank for both strategies so the answer is a number, not a
    belief. A negative result is a valid outcome and should be recorded
    rather than tuned away.
    """
    keyword_rr: list[float] = []
    semantic_rr: list[float] = []
    for case in cases:
        rows = case["rows"]
        relevant = set(case["relevant"])
        words = [w for w in str(case["query"]).lower().split() if w]

        def keyword_score(row: Any, words: list[str] = words) -> float:
            text = row_text(row).lower()
            return sum(1.0 for w in words if w in text)

        semantic = embedder.score_rows(str(case["query"]), rows)

        def semantic_score(row: Any, table: dict[str, float] = semantic) -> float:
            return table.get(row_key(row), 0.0)

        keyword_rr.append(_reciprocal_rank(rows, relevant, keyword_score))
        semantic_rr.append(_reciprocal_rank(rows, relevant, semantic_score))
    return {
        "cases": len(cases),
        "keyword_mrr": round(_mean(keyword_rr), 3),
        "semantic_mrr": round(_mean(semantic_rr), 3),
        "model": embedder.model_id,
        "license": MODEL_LICENSE,
    }


def _reciprocal_rank(rows: list[Any], relevant: set[str], score) -> float:
    ordered = sorted(rows, key=lambda r: (-score(r), row_key(r)))
    for position, row in enumerate(ordered, start=1):
        if row_key(row) in relevant:
            return 1.0 / position
    return 0.0


def _mean(values: list[float]) -> float:
    return math.fsum(values) / len(values) if values else 0.0
