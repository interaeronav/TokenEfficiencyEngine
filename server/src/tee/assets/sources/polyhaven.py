"""Poly Haven backend: keyless, all CC0, the ideal first-class source.

Catalog: api.polyhaven.com/assets?t=… (ETag-served; ~2.3 MB for all
types - fetched once and revalidated, never per search). Files:
api.polyhaven.com/files/<id> with direct CDN URLs + md5 per file.
Model dimensions are millimeters in the catalog; TEE reports meters.
"""

from __future__ import annotations

from tee.assets.sources.base import AssetRow, DownloadPlan, SourceBackend

_API = "https://api.polyhaven.com"
_TYPE_CLASS = {"models": "model", "textures": "material", "hdris": "hdri"}


class PolyHaven(SourceBackend):
    id = "polyhaven"
    display_name = "Poly Haven"
    asset_license_regime = "all CC0-1.0"
    site_tos = (
        "public API; requests must send a unique User-Agent; "
        "'Powered by Poly Haven' credit requested in product docs"
    )
    credit_note = "Powered by Poly Haven (polyhaven.com)"

    def _catalog(self, types: str) -> dict:
        # The type filter is `t=`, NOT `types=`. An unrecognised parameter is
        # ignored and the API answers with EVERY asset, so a model search
        # silently ranked HDRIs and textures alongside meshes (verified live
        # 2026-08-22: ?types=models -> 2361 rows, 989 hdri + 851 texture +
        # 521 model; ?t=models -> 521). The cache key carries the parameter so
        # an old all-types body cannot be revalidated into the filtered slot.
        data, _info = self.store.catalogs.fetch_json(
            f"polyhaven-t-{types}", f"{_API}/assets?t={types}"
        )
        return data

    def search(self, query, *, asset_class=None, limit=20):
        types = {
            "model": "models",
            "material": "textures",
            "texture": "textures",
            "hdri": "hdris",
        }.get(asset_class or "model", "models")
        catalog = self._catalog(types)
        words = [w for w in query.lower().split() if w]
        scored: list[tuple[float, AssetRow]] = []
        for asset_id, info in catalog.items():
            haystack = " ".join(
                [
                    asset_id.lower(),
                    str(info.get("name", "")).lower(),
                    " ".join(info.get("tags", [])),
                    " ".join(info.get("categories", [])),
                ]
            )
            score = self.keyword_score(haystack, words)
            if score <= 0:
                continue
            dims = info.get("dimensions")
            row = AssetRow(
                id=asset_id,
                name=info.get("name", asset_id),
                source=self.id,
                license="CC0-1.0",
                asset_class=_TYPE_CLASS.get(types, "model"),
                tris=info.get("polycount"),
                dims_m=[v / 1000.0 for v in dims] if dims else None,
                tags=list(info.get("tags", []))[:8],
            )
            scored.append((score, row))
        scored.sort(key=lambda pair: -pair[0])
        return [row for _, row in scored[:limit]]

    def thumbnail_url(self, asset_id):
        return f"https://cdn.polyhaven.com/asset_img/thumbs/{asset_id}.png?width=256&height=256"

    def resolve(self, asset_id, *, quality="1k"):
        files_doc, _info = self.store.catalogs.fetch_json(
            f"polyhaven-files-{asset_id}", f"{_API}/files/{asset_id}", ttl_s=7 * 86400
        )
        catalog = {**self._catalog("models"), **self._catalog("textures"), **self._catalog("hdris")}
        info = catalog.get(asset_id, {})
        gltf = files_doc.get("gltf")
        plan_files: list[tuple[str, str, str | None]] = []
        if gltf:
            variant = gltf.get(quality) or gltf.get("1k") or next(iter(gltf.values()))
            main = variant.get("gltf") or {}
            if main.get("url"):
                plan_files.append((f"{asset_id}.gltf", main["url"], main.get("md5")))
            for rel, entry in (main.get("include") or {}).items():
                plan_files.append((rel, entry["url"], entry.get("md5")))
        elif "hdri" in files_doc:
            variant = files_doc["hdri"].get(quality) or next(iter(files_doc["hdri"].values()))
            entry = variant.get("hdr") or variant.get("exr") or {}
            if entry.get("url"):
                name = entry["url"].rsplit("/", 1)[-1]
                plan_files.append((name, entry["url"], entry.get("md5")))
        authors = ", ".join(info.get("authors", {})) or "Poly Haven"
        dims = info.get("dimensions")
        return DownloadPlan(
            source=self.id,
            source_id=asset_id,
            name=info.get("name", asset_id),
            license_id="CC0-1.0",
            files=plan_files,
            attribution={
                "author": authors,
                "url": f"https://polyhaven.com/a/{asset_id}",
            },
            meta={
                "tris": info.get("polycount"),
                "dims_m": [v / 1000.0 for v in dims] if dims else None,
                "class": "model" if gltf else "hdri",
            },
        )
