"""Backend contract: compact rows in, license-gated downloads out.

Each backend declares TWO separate legal facts (A13): the license regime
of its ASSETS and the constraints of its SITE ToS - conflating them is how
"CC0 assets" from a ToS-restricted site end up in a pipeline they may not
be fetched into.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssetRow:
    """One search hit, compact enough to show the model verbatim."""

    id: str  # backend-scoped id
    name: str
    source: str
    license: str  # SPDX (already normalized by the backend)
    asset_class: str  # model | material | hdri | texture
    tris: int | None = None
    dims_m: list[float] | None = None  # [x, y, z] real-world, meters
    tags: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": f"{self.source}:{self.id}",
            "name": self.name,
            "license": self.license,
            "class": self.asset_class,
        }
        if self.tris is not None:
            d["tris"] = self.tris
        if self.dims_m is not None:
            d["dims_m"] = [round(v, 3) for v in self.dims_m]
        return d


@dataclass
class DownloadPlan:
    """Everything needed to fetch and attribute one asset. Files are
    (relative name, url, md5-or-None); URLs are consumed immediately and
    never stored (expiring-URL backends)."""

    source: str
    source_id: str
    name: str
    license_id: str  # raw backend license string; the store gates it
    files: list[tuple[str, str, str | None]]
    attribution: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)


class SourceBackend:
    """Base class; subclasses implement search() and resolve()."""

    id: str = "base"
    display_name: str = "base"
    asset_license_regime: str = ""  # e.g. "all CC0-1.0"
    site_tos: str = ""  # declared constraints on automated use
    credit_note: str | None = None  # e.g. "Powered by Poly Haven"

    def __init__(self, store):
        self.store = store  # AssetStore (catalog cache + gate live there)

    def search(
        self,
        query: str,
        *,
        asset_class: str | None = None,
        limit: int = 20,
    ) -> list[AssetRow]:
        raise NotImplementedError

    def resolve(self, asset_id: str, *, quality: str = "1k") -> DownloadPlan:
        raise NotImplementedError

    def thumbnail_url(self, asset_id: str) -> str | None:
        """Small preview URL for the contact-sheet tie-breaker; None when
        the backend has no cheap thumbnail endpoint."""
        return None

    @staticmethod
    def keyword_score(text: str, words: list[str]) -> float:
        text = text.lower()
        return sum(1.0 for w in words if w in text)
