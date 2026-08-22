"""Content-addressed extraction store (decision A10).

Facts are keyed by (source_media_hash, extractor_id, extractor_version) with
a 2-char fanout layout (the DVC pattern) under `.tee/extract/`. Originals are
referenced by path + hash, never copied (a site video may be gigabytes);
small derived artifacts (thumbnails, keyframes, transcripts) live inside the
store. Re-ingesting identical media is a no-op - a derived-data cache in the
Unreal-DDC sense.

Every fact is a JSON object with an envelope: `kind` (required), and
optionally `frame` (frame id, mandatory for geometric facts), `tier`
(evidence tier), `confidence`, plus kind-specific payload fields.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# Evidence tiers, best first, with default conformance tolerances in meters
# (USIBD LOA-informed; docs/research/18). A comparison's effective tolerance
# is the RSS of both facts' tier tolerances plus transform accuracies.
TIER_TOLERANCE_M: dict[str, float] = {
    "dimension_text": 0.006,  # written dimensions govern (AEC rule)
    "drawing_geometry": 0.012,
    "built_geometry": 0.012,  # what TEE itself constructed in the DCC
    "sfm": 0.030,
    "stated_requirement": 0.0,  # non-geometric
    "gps_prior": 1.5,
    "satellite": 3.0,
    "derived": 0.050,
}

MEDIA_TYPES = {
    ".dxf": "cad",
    ".ifc": "bim",
    ".pdf": "document",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".tif": "image",
    ".tiff": "image",
    ".mp4": "video",
    ".mov": "video",
    ".mkv": "video",
    ".avi": "video",
    ".wav": "audio",
    ".mp3": "audio",
    ".m4a": "audio",
    ".ogg": "audio",
    ".flac": "audio",
    ".srt": "telemetry",
}


def media_type_of(path: Path) -> str:
    return MEDIA_TYPES.get(path.suffix.lower(), "unknown")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ExtractStore:
    def __init__(self, project_root: Path | str):
        self.root = Path(project_root) / ".tee" / "extract"

    # -- source registration -----------------------------------------------

    def source_dir(self, media_hash: str) -> Path:
        return self.root / media_hash[:2] / media_hash[2:]

    def register_source(self, path: Path) -> dict[str, Any]:
        path = Path(path)
        if not path.is_file():
            raise TeeError(
                "no_such_file",
                f"Not a file: {path}",
                fix="Pass an existing file (or a directory to ex_ingest).",
            )
        media_hash = hash_file(path)
        directory = self.source_dir(media_hash)
        directory.mkdir(parents=True, exist_ok=True)
        meta_path = directory / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            if str(path) not in meta["paths"]:
                meta["paths"].append(str(path))
                _write_json(meta_path, meta)
            meta["already_known"] = True
            return meta
        meta = {
            "hash": media_hash,
            "name": path.name,
            "paths": [str(path)],
            "media_type": media_type_of(path),
            "bytes": path.stat().st_size,
            "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        _write_json(meta_path, meta)
        return meta

    def sources(self) -> list[dict[str, Any]]:
        out = []
        if not self.root.exists():
            return out
        for meta_path in sorted(self.root.glob("??/*/meta.json")):
            try:
                out.append(json.loads(meta_path.read_text()))
            except (json.JSONDecodeError, OSError):
                continue
        return out

    def resolve(self, ref: str) -> dict[str, Any]:
        """Find one source by hash prefix (>=6 chars) or file name."""
        matches = [
            s
            for s in self.sources()
            if s["hash"].startswith(ref) or s["name"] == ref or ref in s["name"]
        ]
        if not matches:
            raise TeeError(
                "unknown_source",
                f"No ingested source matches '{ref}'.",
                fix="List sources with ex_sources; ingest with ex_ingest.",
            )
        if len(matches) > 1:
            names = ", ".join(f"{s['hash'][:8]}:{s['name']}" for s in matches[:5])
            raise TeeError(
                "ambiguous_source",
                f"'{ref}' matches {len(matches)} sources.",
                fix=f"Disambiguate with a hash prefix: {names}.",
            )
        return matches[0]

    # -- facts -------------------------------------------------------------

    def facts_path(self, media_hash: str, extractor_id: str, version: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{extractor_id}-{version}")
        return self.source_dir(media_hash) / f"facts-{safe}.json"

    def has_facts(self, media_hash: str, extractor_id: str, version: str) -> bool:
        return self.facts_path(media_hash, extractor_id, version).exists()

    def store_facts(
        self,
        media_hash: str,
        extractor_id: str,
        version: str,
        facts: list[dict[str, Any]],
        *,
        provenance: dict[str, Any] | None = None,
    ) -> int:
        for i, fact in enumerate(facts):
            self.validate_fact(fact, index=i)
        payload = {
            "extractor": extractor_id,
            "version": version,
            "stored_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "provenance": provenance or {},
            "facts": facts,
        }
        path = self.facts_path(media_hash, extractor_id, version)
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, payload)
        return len(facts)

    @staticmethod
    def validate_fact(fact: Any, index: int = 0) -> None:
        if not isinstance(fact, dict) or not isinstance(fact.get("kind"), str):
            raise TeeError(
                "bad_fact",
                f"Fact {index} must be an object with a string 'kind'.",
            )
        tier = fact.get("tier")
        if tier is not None and tier not in TIER_TOLERANCE_M:
            raise TeeError(
                "bad_fact",
                f"Fact {index}: unknown tier '{tier}'.",
                fix=f"Known tiers: {', '.join(TIER_TOLERANCE_M)}.",
            )
        try:
            json.dumps(fact)
        except (TypeError, ValueError) as exc:
            raise TeeError("bad_fact", f"Fact {index} is not JSON-serializable: {exc}") from exc

    def facts(self, media_hash: str, *, kind: str | None = None) -> list[dict[str, Any]]:
        """All facts for one source across extractors, envelope-annotated."""
        out: list[dict[str, Any]] = []
        directory = self.source_dir(media_hash)
        if not directory.exists():
            return out
        for path in sorted(directory.glob("facts-*.json")):
            try:
                payload = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            for fact in payload.get("facts", []):
                if kind and fact.get("kind") != kind:
                    continue
                out.append({**fact, "extractor": payload["extractor"]})
        return out

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Word-overlap search over every stored fact, cheapest thing that
        works; returns compact hits with source references."""
        words = [w for w in re.split(r"[^a-z0-9_.]+", query.lower()) if w]
        scored: list[tuple[float, dict[str, Any]]] = []
        for source in self.sources():
            for fact in self.facts(source["hash"]):
                text = json.dumps(fact, separators=(",", ":")).lower()
                score = sum(1.0 for w in words if w in text)
                if score > 0:
                    scored.append(
                        (
                            score,
                            {
                                "source": source["hash"][:8],
                                "name": source["name"],
                                "fact": fact,
                            },
                        )
                    )
        scored.sort(key=lambda pair: -pair[0])
        return [hit for _, hit in scored[:limit]]

    # -- derived artifacts -------------------------------------------------

    def derived_dir(self, media_hash: str, lane: str) -> Path:
        directory = self.source_dir(media_hash) / lane
        directory.mkdir(parents=True, exist_ok=True)
        return directory


def _write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, default=str))
    tmp.replace(path)
