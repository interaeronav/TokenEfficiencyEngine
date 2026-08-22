"""Input-hash cache (decision A28 requirement 5): the same request never
generates twice. Key = sha256(image bytes) + canonical params + model
revision + product version; a hit returns the stored report verbatim."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

import voxkiln

_ENV_ROOT = "VOXKILN_CACHE"


def cache_root() -> Path:
    root = os.environ.get(_ENV_ROOT)
    if root:
        return Path(root)
    return Path.home() / ".cache" / "voxkiln"


def request_key(image_sha256: str, params: dict[str, Any], model_revision: str | None) -> str:
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256()
    h.update(image_sha256.encode())
    h.update(canonical.encode())
    h.update((model_revision or "unpinned").encode())
    h.update(voxkiln.__version__.encode())
    return h.hexdigest()[:32]


def get(key: str) -> dict[str, Any] | None:
    path = cache_root() / key / "report.json"
    if not path.exists():
        return None
    with open(path) as f:
        report = json.load(f)
    # re-point file paths at the cache copies
    for name, rel in list(report.get("files", {}).items()):
        cached = cache_root() / key / Path(rel).name
        if cached.exists():
            report["files"][name] = str(cached)
    report["cache_hit"] = True
    return report


def put(key: str, report: dict[str, Any]) -> None:
    entry = cache_root() / key
    entry.mkdir(parents=True, exist_ok=True)
    stored = dict(report)
    stored_files = {}
    for name, path in report.get("files", {}).items():
        src = Path(path)
        if src.exists():
            shutil.copy2(src, entry / src.name)
            stored_files[name] = src.name
    stored["files"] = stored_files
    with open(entry / "report.json", "w") as f:
        json.dump(stored, f, indent=1)
