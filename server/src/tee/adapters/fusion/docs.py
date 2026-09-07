"""Version-matched Fusion API docs search (the Blender lane's method).

Hallucinated API calls are the #1 catalogued friction point and the Fusion
API drifts between builds (the bridge's own author lost time to a removed
timer API). So the index is introspected from the LIVE Fusion over the
bridge - 926 of 988 `adsk.fusion` classes carry docstrings and
`inspect.signature` works, measured on 2704.1.53 - cached on disk per Fusion
version, and searched server-side. Results are compact (path + one line + signature); full detail
for one symbol is a separate live call.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tee.kernel.errors import TeeError

if TYPE_CHECKING:
    from tee.adapters.fusion.adapter import FusionAdapter

_MAX_RESULTS = 25


class FusionDocs:
    def __init__(self, adapter: FusionAdapter, cache_dir: Path | str | None = None):
        self.adapter = adapter
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "tee"
        self._entries: list[dict[str, Any]] | None = None
        self._version: str | None = None

    # -- index lifecycle ---------------------------------------------------

    def ensure_index(self) -> int:
        """Load the per-version index, building it from the live Fusion on
        first use. Returns the number of indexed symbols."""
        if self._entries is not None:
            return len(self._entries)
        info = self.adapter.info()
        if not info.connected:
            raise TeeError(
                "fusion_unreachable",
                "Cannot build the API index: no Fusion bridge.",
                fix="Start Fusion (the bridge add-in auto-starts), then retry; check tee_status.",
            )
        version = info.version.split()[0]
        cache_file = self.cache_dir / f"fusion-api-{version}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                self._entries = data["entries"]
                self._version = version
                return len(self._entries)
            except (json.JSONDecodeError, KeyError, OSError):
                cache_file.unlink(missing_ok=True)
        data = self.adapter.docs_index()
        self._entries = list(data.get("entries") or [])
        self._version = version
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"entries": self._entries}))
        tmp.replace(cache_file)
        return len(self._entries)

    # -- queries -----------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        count = self.ensure_index()
        limit = max(1, min(int(limit), _MAX_RESULTS))
        words = [w for w in re.split(r"[^a-z0-9_]+", str(query).lower()) if w]
        if not words:
            raise TeeError(
                "bad_query", "Give one or more keywords.", fix="e.g. 'extrude profile distance'."
            )
        scored: list[tuple[float, dict[str, Any]]] = []
        for entry in self._entries or []:
            path = entry["path"].lower()
            doc = str(entry.get("doc") or "").lower()
            segments = path.split(".")
            score = 0.0
            hits = 0
            for word in words:
                if word in path:
                    hits += 1
                    # an exact segment beats a substring; the last segment beats a class
                    score += 4.0 if word in segments else 2.0
                    if segments[-1] == word:
                        score += 2.0
                elif word in doc:
                    hits += 1
                    score += 1.0
            if hits == len(words) and len(words) > 1:
                score += 3.0  # every word matched somewhere
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda pair: (-pair[0], len(pair[1]["path"]), pair[1]["path"]))
        results = []
        for _, entry in scored[:limit]:
            item: dict[str, Any] = {"path": entry["path"], "kind": entry["kind"]}
            if entry.get("doc"):
                item["doc"] = str(entry["doc"]).splitlines()[0][:140]
            if entry.get("sig"):
                item["sig"] = entry["sig"]
            if "value" in entry:
                item["value"] = entry["value"]
            results.append(item)
        payload: dict[str, Any] = {
            "fusion": self._version,
            "indexed_symbols": count,
            "results": results,
        }
        if not results:
            payload["hint"] = "no matches; try the API noun (Sketch, ExtrudeFeatures, BRepBody)"
        return payload

    def detail(self, path: str) -> dict[str, Any]:
        data = self.adapter.api_detail(path)
        if not data.get("found"):
            suggestions = self.search(path.rsplit(".", 1)[-1], limit=3)["results"]
            hint = ", ".join(s["path"] for s in suggestions) or "fu_search_docs"
            raise TeeError(
                "unknown_api_symbol",
                f"No symbol '{path}' in this Fusion.",
                fix=f"Closest matches: {hint}.",
            )
        return data
