"""HTTP plumbing for asset backends: ETag/TTL-cached catalogs, verified
file downloads. stdlib urllib only - honors HTTPS_PROXY from the
environment by construction.

The prior-art failure this kills structurally: the popular community
integration re-fetches a 2.3 MB catalog on every search. Here a catalog
is fetched once, revalidated with If-None-Match when the backend serves
ETags (Poly Haven does), and TTL-held when it does not (ambientCG - a
one-person project, cache-first out of courtesy as much as efficiency).
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

USER_AGENT = "TokenEfficiencyEngine/0.1 (https://github.com/interaeronav/TokenEfficiencyEngine)"
DEFAULT_TTL_S = 24 * 3600


class CatalogCache:
    """Disk cache for backend catalog/JSON responses under
    `.tee/assets/catalogs/`, keyed by a caller-chosen name."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def _paths(self, name: str) -> tuple[Path, Path]:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
        return self.root / f"{safe}.json", self.root / f"{safe}.meta.json"

    def fetch_json(
        self,
        name: str,
        url: str,
        *,
        ttl_s: int = DEFAULT_TTL_S,
        headers: dict[str, str] | None = None,
        timeout_s: float = 30.0,
    ) -> tuple[Any, dict[str, Any]]:
        """Return (parsed json, cache info). Within TTL the disk copy is
        served without any request; past TTL an ETag revalidation (when the
        backend gave one) turns a fresh copy into a 304 no-payload round
        trip. Offline with a cached copy degrades to the cache + a note."""
        body_path, meta_path = self._paths(name)
        meta: dict[str, Any] = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except (json.JSONDecodeError, OSError):
                meta = {}
        age = time.time() - meta.get("fetched_at", 0)
        if body_path.exists() and age < ttl_s:
            return self._load(body_path), {"cache": "fresh", "age_s": int(age)}

        request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if headers:
            request_headers.update(headers)
        if body_path.exists() and meta.get("etag"):
            request_headers["If-None-Match"] = meta["etag"]
        req = urllib.request.Request(url, headers=request_headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                data = resp.read()
                etag = resp.headers.get("ETag")
        except urllib.error.HTTPError as exc:
            if exc.code == 304 and body_path.exists():
                meta["fetched_at"] = time.time()
                _write(meta_path, json.dumps(meta))
                return self._load(body_path), {"cache": "revalidated-304"}
            raise TeeError(
                "backend_http_error",
                f"{name}: HTTP {exc.code} from {url.split('?')[0]}.",
                fix="Check the backend status / API key; cached data (if any) "
                "is served until then.",
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if body_path.exists():
                return self._load(body_path), {
                    "cache": "stale-offline",
                    "note": f"network unavailable ({exc.__class__.__name__}); serving cache",
                }
            raise TeeError(
                "backend_unreachable",
                f"{name}: cannot reach {url.split('?')[0]} and no cache exists.",
                fix="Connect to the network once to seed the catalog cache.",
            ) from exc
        body_path.parent.mkdir(parents=True, exist_ok=True)
        _write(body_path, data.decode("utf-8", errors="replace"))
        _write(
            meta_path,
            json.dumps({"etag": etag, "url": url, "fetched_at": time.time()}),
        )
        return json.loads(data), {"cache": "miss", "bytes": len(data)}

    @staticmethod
    def _load(path: Path) -> Any:
        return json.loads(path.read_text())


def fetch_bytes(
    url: str, *, headers: dict[str, str] | None = None, timeout_s: float = 120.0
) -> bytes:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TeeError(
            "download_failed",
            f"Download failed: {url.split('?')[0]} ({exc.__class__.__name__}).",
            fix="Retry; if the URL came from a search, re-run the search - "
            "some backends serve expiring URLs.",
        ) from exc


def download_file(
    url: str,
    dest: Path,
    *,
    expected_md5: str | None = None,
    headers: dict[str, str] | None = None,
) -> int:
    """Download to dest (atomically), verifying the md5 when the backend
    published one (Poly Haven does)."""
    data = fetch_bytes(url, headers=headers)
    if expected_md5:
        actual = hashlib.md5(data).hexdigest()
        if actual != expected_md5.lower():
            raise TeeError(
                "checksum_mismatch",
                f"MD5 mismatch for {dest.name}: expected {expected_md5[:12]}…, "
                f"got {actual[:12]}….",
                fix="Retry the download; if it persists the backend catalog is stale.",
            )
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return len(data)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)
