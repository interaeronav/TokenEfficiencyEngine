"""Asset store (A13): content-addressed cache + attribution manifests.

Layout under `.tee/assets/`:
    files/<2ch>/<sha256-rest>/…      cached asset payload files (never URLs -
                                     Sketchfab links expire in 300 s)
    files/<…>/manifest.json          attribution manifest (TASL + SPDX +
                                     license text snapshot)
    index.json                       compact searchable metadata index
    catalogs/                        backend catalog cache (http.CatalogCache)

Every entry passed the license gate BEFORE any file was written; the gate
raising means nothing lands. The attribution manifest travels with the
cache so credits survive re-use across projects and platform churn.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from tee.assets import http as assets_http
from tee.assets.license import LICENSE_TEXT_URLS, LicenseDecision, gate
from tee.kernel.errors import TeeError


class AssetStore:
    def __init__(self, project_root: Path | str, *, allow_sa: bool = False):
        self.root = Path(project_root) / ".tee" / "assets"
        self.allow_sa = allow_sa
        self.catalogs = assets_http.CatalogCache(self.root / "catalogs")
        self._index_path = self.root / "index.json"

    # -- index -------------------------------------------------------------

    def index(self) -> dict[str, dict[str, Any]]:
        if not self._index_path.exists():
            return {}
        try:
            return json.loads(self._index_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self, index: dict[str, dict[str, Any]]) -> None:
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(index, indent=1, sort_keys=True))
        tmp.replace(self._index_path)

    def entry(self, asset_key: str) -> dict[str, Any] | None:
        return self.index().get(asset_key)

    def asset_dir(self, content_hash: str) -> Path:
        return self.root / "files" / content_hash[:2] / content_hash[2:]

    # -- adding assets (the only write path; license-gated) ----------------

    def add_asset(
        self,
        *,
        source: str,
        source_id: str,
        name: str,
        license_id: str | None,
        files: list[tuple[str, bytes]],
        attribution: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
        license_text: str | None = None,
        modifications: str | None = None,
    ) -> dict[str, Any]:
        """Cache one asset: gate the license, write files, write the
        attribution manifest, index it. `files` is [(relative path, bytes)];
        the first file is the primary payload. Returns the index entry."""
        decision: LicenseDecision = gate(license_id, allow_sa=self.allow_sa)
        if not files:
            raise TeeError("no_files", f"Asset '{name}' has no files to cache.")
        digest = hashlib.sha256()
        for rel, data in files:
            digest.update(rel.encode())
            digest.update(data)
        content_hash = digest.hexdigest()
        asset_key = f"{source}:{source_id}"
        directory = self.asset_dir(content_hash)
        primary_rel = files[0][0]
        if not (directory / "manifest.json").exists():
            for rel, data in files:
                target = (directory / rel).resolve()
                if not str(target).startswith(str(directory.resolve())):
                    raise TeeError(
                        "bad_path",
                        f"Refusing path traversal in asset file name '{rel}'.",
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            manifest = self._manifest(
                asset_key=asset_key,
                name=name,
                decision=decision,
                attribution=attribution or {},
                content_hash=content_hash,
                primary=primary_rel,
                license_text=license_text,
                modifications=modifications,
            )
            (directory / "manifest.json").write_text(json.dumps(manifest, indent=1))
        index = self.index()
        entry = {
            "key": asset_key,
            "name": name,
            "source": source,
            "license": decision.spdx,
            "hash": content_hash,
            "primary": primary_rel,
            "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            **(meta or {}),
        }
        if decision.note:
            entry["license_note"] = decision.note
        index[asset_key] = entry
        self._save_index(index)
        return entry

    def _manifest(
        self,
        *,
        asset_key: str,
        name: str,
        decision: LicenseDecision,
        attribution: dict[str, Any],
        content_hash: str,
        primary: str,
        license_text: str | None,
        modifications: str | None,
    ) -> dict[str, Any]:
        """TASL (Title, Author, Source, License) + SPDX + snapshot (A13)."""
        author = attribution.get("author") or "unknown"
        source_url = attribution.get("url") or ""
        text, text_origin = license_text, "backend"
        if text is None:
            text, text_origin = self._snapshot_license_text(decision.spdx)
        credit = f'"{name}" by {author}'
        if source_url:
            credit += f" ({source_url})"
        credit += f", licensed {decision.spdx}"
        if modifications:
            credit += f"; modified: {modifications}"
        return {
            "title": name,
            "author": author,
            "source_url": source_url,
            "license_spdx": decision.spdx,
            "license_url": LICENSE_TEXT_URLS.get(decision.spdx, ""),
            "license_text_snapshot": text,
            "license_text_origin": text_origin,
            "attribution_required": decision.attribution_required,
            "asset_key": asset_key,
            "file_hash": content_hash,
            "primary_file": primary,
            "modifications": modifications or "none",
            "retrieved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "credit_line": credit,
        }

    def _snapshot_license_text(self, spdx: str) -> tuple[str | None, str]:
        url = LICENSE_TEXT_URLS.get(spdx)
        if not url:
            return None, "unavailable"
        try:
            text = assets_http.fetch_bytes(url, timeout_s=15).decode("utf-8", errors="replace")
            return text, "snapshot"
        except TeeError:
            # Offline is not a reason to refuse a *gated* license; record
            # the canonical URL so the snapshot can be completed later.
            return None, f"offline; canonical text at {url}"

    # -- reads -------------------------------------------------------------

    def manifest(self, asset_key: str) -> dict[str, Any]:
        entry = self.entry(asset_key)
        if entry is None:
            raise TeeError(
                "unknown_asset",
                f"No cached asset '{asset_key}'.",
                fix="Search with as_search; cache via as_import.",
            )
        path = self.asset_dir(entry["hash"]) / "manifest.json"
        return json.loads(path.read_text())

    def primary_path(self, asset_key: str) -> Path:
        entry = self.entry(asset_key)
        if entry is None:
            raise TeeError(
                "unknown_asset",
                f"No cached asset '{asset_key}'.",
                fix="Search with as_search; cache via as_import.",
            )
        return self.asset_dir(entry["hash"]) / entry["primary"]

    def credits_markdown(self) -> str:
        """CREDITS.md for every cached asset that requires (or deserves)
        attribution; CC0 entries are listed as courtesy credits."""
        lines = [
            "# Asset credits",
            "",
            "Generated by TEE from per-asset attribution manifests.",
            "",
        ]
        required: list[str] = []
        courtesy: list[str] = []
        for key in sorted(self.index()):
            try:
                manifest = self.manifest(key)
            except (TeeError, OSError, json.JSONDecodeError):
                continue
            line = f"- {manifest['credit_line']}"
            if manifest.get("attribution_required"):
                required.append(line)
            else:
                courtesy.append(line)
        if required:
            lines += ["## Required attribution", "", *required, ""]
        if courtesy:
            lines += ["## Courtesy credits (CC0 / public domain)", "", *courtesy, ""]
        if not required and not courtesy:
            lines.append("No cached assets yet.")
        return "\n".join(lines)

    def write_credits(self, out_path: Path | None = None) -> Path:
        path = out_path or (self.root / "CREDITS.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.credits_markdown())
        return path
