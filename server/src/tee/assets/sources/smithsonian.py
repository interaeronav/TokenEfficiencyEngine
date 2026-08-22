"""Smithsonian Open Access backend: api.data.gov key, CC0-flag-GATED -
only records whose usage flag is explicitly CC0 pass (the collection also
holds rights-reserved media; the flag decides, never the collection)."""

from __future__ import annotations

from typing import Any

from tee.assets.sources.base import AssetRow, DownloadPlan, SourceBackend
from tee.kernel.errors import TeeError

_API = "https://api.si.edu/openaccess/api/v1.0"


class Smithsonian(SourceBackend):
    id = "smithsonian"
    display_name = "Smithsonian Open Access"
    asset_license_regime = "CC0-1.0 subset only (usage flag gated per record)"
    site_tos = "api.data.gov key required; rate limits apply"

    def __init__(self, store, api_key: str):
        super().__init__(store)
        self.api_key = api_key

    def search(self, query, *, asset_class=None, limit=20):
        if asset_class not in (None, "model"):
            return []
        data, _info = self.store.catalogs.fetch_json(
            f"smithsonian-{query.replace(' ', '_')[:40]}",
            f"{_API}/search?q={query.replace(' ', '+')}"
            f"+online_media_type:%223D+Images%22&rows={min(limit * 2, 50)}"
            f"&api_key={self.api_key}",
            ttl_s=7 * 86400,
        )
        rows = []
        for record in (data.get("response", {}).get("rows", []) or [])[: limit * 2]:
            content = record.get("content", {})
            if not _is_cc0(content):
                continue  # fail closed: no explicit CC0 flag, no row
            rows.append(
                AssetRow(
                    id=record.get("id", ""),
                    name=record.get("title", "untitled"),
                    source=self.id,
                    license="CC0-1.0",
                    asset_class="model",
                )
            )
            if len(rows) >= limit:
                break
        return rows

    def resolve(self, asset_id, *, quality="1k"):
        data, _info = self.store.catalogs.fetch_json(
            f"smithsonian-content-{asset_id[:40]}",
            f"{_API}/content/{asset_id}?api_key={self.api_key}",
            ttl_s=7 * 86400,
        )
        content = data.get("response", {}).get("content", {})
        if not _is_cc0(content):
            raise TeeError(
                "license_blocked",
                f"Smithsonian record {asset_id} is not flagged CC0.",
                fix="Only CC0-flagged records are usable; pick another hit.",
            )
        files: list[tuple[str, str, str | None]] = []
        media = content.get("descriptiveNonRepeating", {}).get("online_media", {}).get("media", [])
        for item in media:
            for resource in item.get("resources", []) or []:
                url = resource.get("url", "")
                if url.endswith((".glb", ".gltf", ".obj", ".stl")):
                    files.append((url.rsplit("/", 1)[-1], url, None))
        title = content.get("descriptiveNonRepeating", {}).get("title", {})
        name = title.get("content", asset_id) if isinstance(title, dict) else asset_id
        return DownloadPlan(
            source=self.id,
            source_id=asset_id,
            name=name,
            license_id="CC0-1.0",
            files=files,
            attribution={
                "author": "Smithsonian Institution",
                "url": f"https://si.edu/object/{asset_id}",
            },
            meta={"class": "model"},
        )


def _is_cc0(content: dict[str, Any]) -> bool:
    usage = content.get("descriptiveNonRepeating", {}).get("metadata_usage", {})
    return str(usage.get("access", "")).upper() == "CC0"
