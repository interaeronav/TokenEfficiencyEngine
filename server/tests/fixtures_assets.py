"""Shared asset-test fixtures: a tiny programmatic GLB builder (known
extents and tri counts, no binary blobs checked into the repo) and a fake
source backend."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from tee.assets.sources.base import AssetRow, DownloadPlan, SourceBackend


def build_glb(
    path: Path,
    *,
    size: tuple[float, float, float] = (1.0, 1.0, 1.0),
    scale: float = 1.0,
    tris: int = 12,
) -> Path:
    """Write a minimal valid .glb: one mesh whose POSITION accessor min/max
    spans `size` (before the node `scale`), with `tris` triangles declared
    via an index accessor. Geometry buffers are zero-filled - the probe
    reads only the JSON header, which is the point."""
    sx, sy, sz = size
    index_count = tris * 3
    buffer_bytes = index_count * 2
    doc = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "scale": [scale, scale, scale]}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}]}],
        "accessors": [
            {
                "componentType": 5126,
                "count": 8,
                "type": "VEC3",
                "min": [-sx / 2, 0.0, -sz / 2],
                "max": [sx / 2, sy, sz / 2],
            },
            {"componentType": 5123, "count": index_count, "type": "SCALAR"},
        ],
        "bufferViews": [{"buffer": 0, "byteLength": buffer_bytes}],
        "buffers": [{"byteLength": buffer_bytes}],
        "materials": [{"name": "mat"}],
    }
    json_bytes = json.dumps(doc, separators=(",", ":")).encode()
    json_bytes += b" " * (-len(json_bytes) % 4)
    bin_bytes = b"\x00" * buffer_bytes
    bin_bytes += b"\x00" * (-len(bin_bytes) % 4)
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    with open(path, "wb") as fh:
        fh.write(b"glTF" + struct.pack("<II", 2, total))
        fh.write(struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes)
        fh.write(struct.pack("<I4s", len(bin_bytes), b"BIN\x00") + bin_bytes)
    return path


class FakeBackend(SourceBackend):
    """In-memory backend for search/import tests: rows + downloadable bytes
    with per-asset licenses (including deliberately blocked ones)."""

    id = "fakesource"
    display_name = "Fake Source"
    asset_license_regime = "mixed (test)"
    site_tos = "none"

    def __init__(self, store, rows=None, licenses=None):
        super().__init__(store)
        self.rows = rows or []
        self.licenses = licenses or {}

    def search(self, query, *, asset_class=None, limit=20):
        words = query.lower().split()
        hits = [
            r
            for r in self.rows
            if (asset_class in (None, r.asset_class))
            and any(w in r.name.lower() or w in " ".join(r.tags) for w in words)
        ]
        return hits[:limit]

    def resolve(self, asset_id, *, quality="1k"):
        row = next((r for r in self.rows if r.id == asset_id), None)
        if row is None:
            raise KeyError(asset_id)
        return DownloadPlan(
            source=self.id,
            source_id=asset_id,
            name=row.name,
            license_id=self.licenses.get(asset_id, row.license),
            files=[(f"{asset_id}.glb", f"fake://{asset_id}", None)],
            attribution={"author": "Test Author", "url": f"https://example.test/{asset_id}"},
            meta={"tris": row.tris, "dims_m": row.dims_m, "class": row.asset_class},
        )


def make_rows() -> list[AssetRow]:
    return [
        AssetRow(
            id="sofa1",
            name="Big Sofa",
            source="fakesource",
            license="CC0-1.0",
            asset_class="model",
            tris=9000,
            dims_m=[2.1, 0.9, 0.8],
            tags=["sofa", "seating", "fabric"],
        ),
        AssetRow(
            id="chair1",
            name="Wood Chair",
            source="fakesource",
            license="CC-BY-4.0",
            asset_class="model",
            tris=4000,
            dims_m=[0.5, 0.55, 0.9],
            tags=["chair", "seating", "wood"],
        ),
        AssetRow(
            id="ncchair",
            name="NC Chair",
            source="fakesource",
            license="CC-BY-NC-4.0",
            asset_class="model",
            tris=100,
            dims_m=[0.5, 0.5, 0.9],
            tags=["chair", "nc"],
        ),
    ]
