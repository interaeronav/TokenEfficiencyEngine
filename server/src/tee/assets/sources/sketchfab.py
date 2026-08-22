"""Sketchfab backend - GUARDED opt-in (A13).

Platform risk is explicit: KitBash acquired Sketchfab + ArtStation from
Epic on 2026-08-10; download URLs expire in 300 seconds (cache the FILE,
never the URL); licenses are per-model and must be gated per asset. Off by
default; enabled only by `[assets] sketchfab = true` plus a user OAuth
token. Search works tokenless (public API); download requires the token.
"""

from __future__ import annotations

from tee.assets.sources.base import AssetRow, DownloadPlan, SourceBackend
from tee.kernel.errors import TeeError

_API = "https://api.sketchfab.com/v3"

_LICENSES = {
    "cc0": "CC0-1.0",
    "by": "CC-BY-4.0",
    "by-sa": "CC-BY-SA-4.0",
    # by-nd / by-nc* deliberately unmapped: the gate blocks them.
}


class Sketchfab(SourceBackend):
    id = "sketchfab"
    display_name = "Sketchfab"
    asset_license_regime = "per-model CC licenses incl. NC/ND (gated per asset)"
    site_tos = (
        "OAuth per-user for downloads; URLs expire in 300 s; strict "
        "attribution display rules; platform ownership changed 2026-08 "
        "(KitBash) - treat ToS as volatile"
    )

    def __init__(self, store, token: str | None = None):
        super().__init__(store)
        self.token = token

    def search(self, query, *, asset_class=None, limit=20):
        if asset_class not in (None, "model"):
            return []
        data, _info = self.store.catalogs.fetch_json(
            f"sketchfab-{query.replace(' ', '_')[:40]}",
            f"{_API}/search?type=models&downloadable=true&q={query.replace(' ', '+')}"
            f"&count={min(limit, 24)}",
            ttl_s=86400,
        )
        rows = []
        for hit in data.get("results", [])[:limit]:
            slug = (hit.get("license") or {}).get("slug", "")
            spdx = _LICENSES.get(slug, slug or "unknown")
            rows.append(
                AssetRow(
                    id=hit.get("uid", ""),
                    name=hit.get("name", "untitled"),
                    source=self.id,
                    license=spdx,
                    asset_class="model",
                    tris=hit.get("faceCount"),
                    tags=[t.get("slug", "") for t in hit.get("tags", [])][:8],
                )
            )
        return rows

    def resolve(self, asset_id, *, quality="1k"):
        if not self.token:
            raise TeeError(
                "sketchfab_token_missing",
                "Sketchfab downloads need a user OAuth token.",
                fix="Set TEE_SKETCHFAB_TOKEN (or [assets] sketchfab_token); "
                "search works without one.",
            )
        headers = {"Authorization": f"Token {self.token}"}
        model, _ = self.store.catalogs.fetch_json(
            f"sketchfab-model-{asset_id}", f"{_API}/models/{asset_id}", ttl_s=86400
        )
        slug = (model.get("license") or {}).get("slug", "")
        spdx = _LICENSES.get(slug, slug or "unknown")
        # download URLs expire in 300 s: fetch fresh, bypass the cache
        download, _ = self.store.catalogs.fetch_json(
            f"sketchfab-dl-{asset_id}",
            f"{_API}/models/{asset_id}/download",
            ttl_s=0,
            headers=headers,
        )
        gltf_url = (download.get("gltf") or {}).get("url")
        files = [(f"{asset_id}.zip", gltf_url, None)] if gltf_url else []
        author = (model.get("user") or {}).get("displayName", "unknown")
        return DownloadPlan(
            source=self.id,
            source_id=asset_id,
            name=model.get("name", asset_id),
            license_id=spdx,
            files=files,
            attribution={
                "author": author,
                "url": model.get("viewerUrl", f"https://sketchfab.com/3d-models/{asset_id}"),
            },
            meta={"tris": model.get("faceCount"), "class": "model"},
            headers=headers,
        )
