"""Poly Pizza backend: API key, GLB models, mixed CC0/CC-BY with per-asset
license fields - every hit passes the per-asset license through the gate
(never a blanket assumption)."""

from __future__ import annotations

from tee.assets.sources.base import AssetRow, DownloadPlan, SourceBackend
from tee.kernel.errors import TeeError

_API = "https://api.poly.pizza/v1.1"

# Poly Pizza license field -> SPDX (per-asset; anything unmapped is passed
# through raw and the gate blocks it).
_LICENSES = {
    "CC0": "CC0-1.0",
    "CC-BY": "CC-BY-4.0",
    "CC BY": "CC-BY-4.0",
    "CREATIVE COMMONS ATTRIBUTION": "CC-BY-4.0",
}


class PolyPizza(SourceBackend):
    id = "polypizza"
    display_name = "Poly Pizza"
    asset_license_regime = "mixed CC0-1.0 / CC-BY-4.0, per-asset field"
    site_tos = "API key required; rate limits apply"

    def __init__(self, store, api_key: str):
        super().__init__(store)
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"x-auth-token": self.api_key}

    def search(self, query, *, asset_class=None, limit=20):
        if asset_class not in (None, "model"):
            return []
        data, _info = self.store.catalogs.fetch_json(
            f"polypizza-{query.replace(' ', '_')[:40]}",
            f"{_API}/search/{query.replace(' ', '%20')}?Limit={min(limit, 32)}",
            ttl_s=86400,
            headers=self._headers(),
        )
        rows = []
        for hit in data.get("results", [])[:limit]:
            spdx = _LICENSES.get(str(hit.get("Licence", "")).upper().strip(), "")
            rows.append(
                AssetRow(
                    id=str(hit.get("ID")),
                    name=hit.get("Title", "untitled"),
                    source=self.id,
                    license=spdx or str(hit.get("Licence", "unknown")),
                    asset_class="model",
                    tris=hit.get("TriCount"),
                    tags=[t for t in (hit.get("Tags") or []) if isinstance(t, str)][:8],
                )
            )
        return rows

    def resolve(self, asset_id, *, quality="1k"):
        data, _info = self.store.catalogs.fetch_json(
            f"polypizza-model-{asset_id}",
            f"{_API}/model/{asset_id}",
            ttl_s=86400,
            headers=self._headers(),
        )
        url = data.get("Download")
        if not url:
            raise TeeError(
                "no_download",
                f"Poly Pizza model {asset_id} has no download URL.",
                fix="Re-run as_search; the asset may have been removed.",
            )
        creator = (data.get("Creator") or {}).get("Username", "unknown")
        spdx = _LICENSES.get(str(data.get("Licence", "")).upper().strip(), "")
        return DownloadPlan(
            source=self.id,
            source_id=str(asset_id),
            name=data.get("Title", asset_id),
            license_id=spdx or str(data.get("Licence", "")),
            files=[(f"{asset_id}.glb", url, None)],
            attribution={
                "author": creator,
                "url": f"https://poly.pizza/m/{asset_id}",
            },
            meta={"tris": data.get("TriCount"), "class": "model"},
            headers=self._headers(),
        )
