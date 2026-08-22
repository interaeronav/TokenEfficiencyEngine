"""ambientCG backend: keyless, all CC0 PBR material scans.

One-person project: cache-first is a courtesy as much as an optimization
(TTL-held catalog; the API serves no ETag). Downloads are zip bundles per
resolution; TEE fetches the smallest that satisfies the request.
"""

from __future__ import annotations

from tee.assets.sources.base import AssetRow, DownloadPlan, SourceBackend

_API = "https://ambientcg.com/api/v2/full_json"


class AmbientCG(SourceBackend):
    id = "ambientcg"
    display_name = "ambientCG"
    asset_license_regime = "all CC0-1.0"
    site_tos = "public API; cache-first requested (small operator); no bulk scraping"
    credit_note = "Materials by ambientCG (ambientcg.com), CC0"

    def _catalog(self, query: str) -> list[dict]:
        url = (
            f"{_API}?type=Material&limit=100&include=downloadData,displayData,dimensionData"
            f"&q={query.replace(' ', '+')}"
        )
        data, _info = self.store.catalogs.fetch_json(
            f"ambientcg-{query.replace(' ', '_')[:40]}", url, ttl_s=7 * 86400
        )
        return data.get("foundAssets", [])

    def search(self, query, *, asset_class=None, limit=20):
        if asset_class not in (None, "material", "texture"):
            return []
        rows = []
        for asset in self._catalog(query)[:limit]:
            dims = None
            dim_x, dim_y = asset.get("dimensionX"), asset.get("dimensionY")
            if dim_x and dim_y:
                # catalog dimensions are centimeters of covered surface
                dims = [float(dim_x) / 100.0, float(dim_y) / 100.0, 0.0]
            rows.append(
                AssetRow(
                    id=asset["assetId"],
                    name=asset.get("displayName") or asset["assetId"],
                    source=self.id,
                    license="CC0-1.0",
                    asset_class="material",
                    dims_m=dims,
                    tags=list(asset.get("tags", []))[:8],
                )
            )
        return rows

    def resolve(self, asset_id, *, quality="1k"):
        assets = self._catalog(asset_id)
        match = next((a for a in assets if a["assetId"] == asset_id), None)
        if match is None:
            # targeted query (the cached listing may not contain the id)
            match = next(
                (a for a in self._catalog(asset_id) if a["assetId"] == asset_id), None
            )
        files: list[tuple[str, str, str | None]] = []
        if match:
            folders = (match.get("downloadFolders") or {}).get("default", {})
            attrs = folders.get("downloadFiletypeCategories", {}).get("zip", {})
            downloads = attrs.get("downloads", [])
            wanted = f"{quality.upper()}-JPG"
            chosen = next(
                (d for d in downloads if d.get("attribute") == wanted),
                downloads[0] if downloads else None,
            )
            if chosen and chosen.get("downloadLink"):
                files.append((f"{asset_id}_{quality}.zip", chosen["downloadLink"], None))
        return DownloadPlan(
            source=self.id,
            source_id=asset_id,
            name=(match or {}).get("displayName") or asset_id,
            license_id="CC0-1.0",
            files=files,
            attribution={
                "author": "ambientCG",
                "url": f"https://ambientcg.com/view?id={asset_id}",
            },
            meta={"class": "material"},
        )
