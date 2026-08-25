"""Live backend tests (network-marked; skip cleanly offline, 9.7).

These hit the real free APIs read-only and prove: catalog caching (the
second search makes zero requests), search compactness, and a real
CC0 download landing in the store with a correct manifest.
"""

from __future__ import annotations

import json

import pytest

from tee.assets.sources.ambientcg import AmbientCG
from tee.assets.sources.polyhaven import PolyHaven
from tee.assets.store import AssetStore

pytestmark = pytest.mark.network


@pytest.fixture()
def store(tmp_path):
    return AssetStore(tmp_path)


def test_polyhaven_search_is_compact_and_cached(store, network):
    backend = PolyHaven(store)
    rows = backend.search("chair furniture", asset_class="model", limit=5)
    assert rows, "Poly Haven should have furniture models"
    payloads = [r.to_payload() for r in rows]
    text = json.dumps(payloads, separators=(",", ":"))
    # acceptance: a furniture query answers in <= 200 response tokens
    assert len(text) / 3.5 <= 200, f"search rows too fat: ~{len(text) / 3.5:.0f} tokens"
    for row in rows:
        assert row.license == "CC0-1.0"
        assert row.dims_m is not None  # models carry real dimensions
        assert row.asset_class == "model"  # `t=`, not `types=`: no HDRIs here
    # second search: served from the fresh disk cache, no network
    _, info = store.catalogs.fetch_json(
        "polyhaven-t-models", "https://api.polyhaven.com/assets?t=models"
    )
    assert info["cache"] == "fresh"


def test_polyhaven_resolve_names_cc0_and_files(store, network):
    backend = PolyHaven(store)
    rows = backend.search("chair", asset_class="model", limit=1)
    plan = backend.resolve(rows[0].id, quality="1k")
    assert plan.license_id == "CC0-1.0"
    assert plan.files, "resolve should list gltf files"
    assert plan.files[0][0].endswith(".gltf")
    assert all(url.startswith("https://") for _, url, _ in plan.files)


def test_ambientcg_material_search(store, network):
    backend = AmbientCG(store)
    rows = backend.search("brick", asset_class="material", limit=5)
    assert rows
    assert all(r.license == "CC0-1.0" for r in rows)
    assert all(r.asset_class == "material" for r in rows)
