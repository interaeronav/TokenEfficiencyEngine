"""Faceted asset search + server-side ranking (A15).

The Holodeck contract: the model states WHAT it needs (description, class,
target dims, constraints); everything heavy happens here - keyword rank
first, ΔE00 palette-vs-style-brief second, thumbnail embeddings third
(optional hook, index-time). The model sees ≤5 compact rows per class,
never a catalog.
"""

from __future__ import annotations

from typing import Any

from tee.assets.color import palette_distance
from tee.assets.license import normalize_spdx
from tee.assets.sources.base import AssetRow


class AssetSearch:
    def __init__(self, store, backends: dict[str, Any], *, embedder=None):
        self.store = store
        self.backends = backends
        self.embedder = embedder  # optional [assets-embed] hook: (row) -> score

    def search(
        self,
        query: str,
        *,
        asset_class: str | None = None,
        license_filter: str | None = None,
        max_tris: int | None = None,
        dims_range: list[list[float]] | None = None,  # [[min x,y,z],[max x,y,z]]
        style_palette: list[list[float]] | None = None,  # Lab rows from the brief
        limit: int = 5,
        backends: list[str] | None = None,
    ) -> dict[str, Any]:
        rows: list[AssetRow] = []
        errors: list[str] = []
        for name, backend in self.backends.items():
            if backends and name not in backends:
                continue
            try:
                rows.extend(backend.search(query, asset_class=asset_class, limit=limit * 4))
            except Exception as exc:  # one backend down must not kill the search
                errors.append(f"{name}: {getattr(exc, 'message', exc)}")
        rows.extend(self._local_rows(query, asset_class))

        rows = self._facet(rows, license_filter, max_tris, dims_range)
        ranked = self._rank(rows, query, style_palette)

        by_class: dict[str, list[dict[str, Any]]] = {}
        for row in ranked:
            bucket = by_class.setdefault(row.asset_class, [])
            if len(bucket) < limit:
                bucket.append(row.to_payload())
        out: dict[str, Any] = {"query": query, "results": by_class}
        if errors:
            out["backend_errors"] = errors
        cached = {r.id for r in rows if f"{r.source}:{r.id}" in self.store.index()}
        if cached:
            out["already_cached"] = sorted(f"{r.source}:{r.id}" for r in rows if r.id in cached)
        return out

    # -- internals ---------------------------------------------------------

    def _local_rows(self, query: str, asset_class: str | None) -> list[AssetRow]:
        words = [w for w in query.lower().split() if w]
        rows = []
        for key, entry in self.store.index().items():
            if entry.get("source") != "local":
                continue
            if asset_class and entry.get("class") != asset_class:
                continue
            haystack = f"{entry.get('name', '')} {key}".lower()
            if not any(w in haystack for w in words):
                continue
            rows.append(
                AssetRow(
                    id=entry["name"],
                    name=entry["name"],
                    source="local",
                    license="local",
                    asset_class=entry.get("class", "model"),
                    tris=entry.get("tris"),
                    dims_m=entry.get("dims_m"),
                )
            )
        return rows

    @staticmethod
    def _facet(
        rows: list[AssetRow],
        license_filter: str | None,
        max_tris: int | None,
        dims_range: list[list[float]] | None,
    ) -> list[AssetRow]:
        out = []
        for row in rows:
            if license_filter:
                spdx = normalize_spdx(row.license) or row.license
                if spdx != license_filter and row.license != "local":
                    continue
            if max_tris and row.tris and row.tris > max_tris:
                continue
            if dims_range and row.dims_m:
                lo, hi = dims_range
                sorted_row = sorted(row.dims_m)
                sorted_lo, sorted_hi = sorted(lo), sorted(hi)
                if any(
                    d < sorted_lo[i] * 0.9 or d > sorted_hi[i] * 1.1
                    for i, d in enumerate(sorted_row)
                ):
                    continue
            out.append(row)
        return out

    def _rank(
        self,
        rows: list[AssetRow],
        query: str,
        style_palette: list[list[float]] | None,
    ) -> list[AssetRow]:
        words = [w for w in query.lower().split() if w]

        def score(row: AssetRow) -> float:
            text = f"{row.name} {' '.join(row.tags)}".lower()
            keyword = sum(1.0 for w in words if w in text)
            palette_bonus = 0.0
            if style_palette:
                labs = self._asset_palette(row)
                if labs:
                    distance = palette_distance(labs, [tuple(p) for p in style_palette])
                    palette_bonus = max(0.0, (40.0 - distance) / 40.0)  # ΔE00 40 = unrelated
            embed_bonus = 0.0
            if self.embedder is not None:
                try:
                    embed_bonus = float(self.embedder(row))
                except Exception:
                    embed_bonus = 0.0
            return keyword * 2.0 + palette_bonus + embed_bonus

        return sorted(rows, key=lambda r: (-score(r), r.source, r.id))

    def _asset_palette(self, row: AssetRow) -> list[tuple[float, float, float]] | None:
        """Palette for ranking: local material sets expose their base-color
        map; cached thumbnails are used when present. Index-time work only -
        never a network fetch inside ranking."""
        entry = self.store.index().get(f"{row.source}:{row.id}")
        if not entry:
            return None
        labs = entry.get("palette_lab")
        if labs:
            return [tuple(v) for v in labs]
        maps = entry.get("maps") or {}
        base = maps.get("base_color")
        if base:
            try:
                from tee.assets.color import image_palette

                facts = image_palette(base, k=4)
            except Exception:
                return None
            labs = [tuple(f["lab"]) for f in facts]
            entry["palette_lab"] = [list(v) for v in labs]
            index = self.store.index()
            index[f"{row.source}:{row.id}"] = entry
            self.store._save_index(index)
            return labs
        return None
