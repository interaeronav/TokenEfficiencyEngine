"""Phase 9.1: license gate, asset store + attribution, glTF probe, ingest."""

from __future__ import annotations

import json

import pytest
from fixtures_assets import build_glb

from tee.assets import gltf
from tee.assets.license import gate, normalize_spdx
from tee.assets.store import AssetStore
from tee.kernel.errors import TeeError

CC0_TEXT = "CC0 1.0 Universal (test snapshot)"


# -- license gate ----------------------------------------------------------


def test_gate_allows_cc0_and_by():
    assert gate("CC0-1.0").spdx == "CC0-1.0"
    assert gate("CC0-1.0").attribution_required is False
    decision = gate("CC-BY-4.0")
    assert decision.attribution_required is True


def test_gate_normalizes_aliases():
    assert normalize_spdx("cc0") == "CC0-1.0"
    assert normalize_spdx("Public Domain") == "CC-PDDC"
    assert gate("cc by 4.0").spdx == "CC-BY-4.0"


@pytest.mark.parametrize(
    "blocked",
    ["CC-BY-NC-4.0", "CC-BY-ND-4.0", "GPL-3.0-only", "unknown", "", None, "All Rights Reserved"],
)
def test_gate_fails_closed(blocked):
    with pytest.raises(TeeError) as err:
        gate(blocked)
    assert err.value.code == "license_blocked"


def test_gate_sa_needs_opt_in():
    with pytest.raises(TeeError):
        gate("CC-BY-SA-4.0")
    decision = gate("CC-BY-SA-4.0", allow_sa=True)
    assert decision.attribution_required and "share-alike" in (decision.note or "")


# -- store + attribution ---------------------------------------------------


def _add(store: AssetStore, license_id: str = "CC0-1.0", key: str = "a1"):
    return store.add_asset(
        source="fakesource",
        source_id=key,
        name=f"Asset {key}",
        license_id=license_id,
        files=[(f"{key}.glb", b"payload-" + key.encode())],
        attribution={"author": "Jane Maker", "url": f"https://example.test/{key}"},
        meta={"tris": 100, "class": "model"},
        license_text=CC0_TEXT,
    )


def test_store_roundtrip_and_manifest(tmp_path):
    store = AssetStore(tmp_path)
    entry = _add(store)
    assert store.entry("fakesource:a1") == entry
    manifest = store.manifest("fakesource:a1")
    assert manifest["author"] == "Jane Maker"
    assert manifest["license_spdx"] == "CC0-1.0"
    assert manifest["license_text_snapshot"] == CC0_TEXT
    assert manifest["file_hash"] == entry["hash"]
    assert store.primary_path("fakesource:a1").read_bytes() == b"payload-a1"


def test_nc_asset_never_enters_cache(tmp_path):
    """The acceptance test: an NC-licensed asset is refused BEFORE any file
    is written."""
    store = AssetStore(tmp_path)
    with pytest.raises(TeeError) as err:
        _add(store, license_id="CC-BY-NC-4.0", key="evil")
    assert err.value.code == "license_blocked"
    assert store.index() == {}
    files_root = store.root / "files"
    assert not files_root.exists() or not any(files_root.rglob("*.glb"))


def test_credits_renderer(tmp_path):
    store = AssetStore(tmp_path)
    _add(store, "CC0-1.0", "zero")
    _add(store, "CC-BY-4.0", "by")
    text = store.credits_markdown()
    assert "## Required attribution" in text
    assert '"Asset by" by Jane Maker' in text
    assert "licensed CC-BY-4.0" in text
    assert "## Courtesy credits" in text
    path = store.write_credits(tmp_path / "CREDITS.md")
    assert path.read_text() == text


def test_store_blocks_path_traversal(tmp_path):
    store = AssetStore(tmp_path)
    with pytest.raises(TeeError) as err:
        store.add_asset(
            source="fakesource",
            source_id="zip",
            name="Zip Slip",
            license_id="CC0-1.0",
            files=[("../../escape.glb", b"x")],
            license_text=CC0_TEXT,
        )
    assert err.value.code == "bad_path"


def test_sa_store_flag(tmp_path):
    store = AssetStore(tmp_path, allow_sa=True)
    entry = _add(store, "CC-BY-SA-4.0", "sa1")
    assert "share-alike" in entry["license_note"]


# -- glTF probe ------------------------------------------------------------


def test_glb_probe_extents_and_tris(tmp_path):
    path = build_glb(tmp_path / "chair.glb", size=(0.5, 0.9, 0.6), tris=250)
    probed = gltf.probe(path)
    assert probed["triangles"] == 250
    assert probed["units"] == "m"
    # glTF Y-up: authored extents [x=0.5, y=0.9, z=0.6]
    assert probed["extents_m"] == pytest.approx([0.5, 0.9, 0.6])
    # Z-up view swaps Y and Z: [0.5, 0.6, 0.9]
    assert probed["dims_zup_m"] == pytest.approx([0.5, 0.6, 0.9])


def test_glb_probe_composes_node_scale(tmp_path):
    path = build_glb(tmp_path / "big.glb", size=(1.0, 1.0, 1.0), scale=2.5, tris=12)
    probed = gltf.probe(path)
    assert probed["extents_m"] == pytest.approx([2.5, 2.5, 2.5])


def test_gltf_json_probe(tmp_path):
    doc = {
        "asset": {"version": "2.0"},
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "mode": 4}]}],
        "accessors": [
            {
                "componentType": 5126,
                "count": 300,
                "type": "VEC3",
                "min": [0, 0, 0],
                "max": [2.0, 1.0, 0.1],
            }
        ],
    }
    path = tmp_path / "wall.gltf"
    path.write_text(json.dumps(doc))
    probed = gltf.probe(path)
    assert probed["triangles"] == 100  # un-indexed: POSITION count / 3
    assert probed["extents_m"] == pytest.approx([2.0, 1.0, 0.1])


def test_probe_rejects_non_gltf(tmp_path):
    bad = tmp_path / "model.fbx"
    bad.write_bytes(b"not gltf")
    with pytest.raises(TeeError):
        gltf.probe(bad)


# -- local ingest ----------------------------------------------------------


def test_ingest_directory(tmp_path):
    from tee.assets.ingest import ingest_directory

    lib = tmp_path / "library"
    lib.mkdir()
    build_glb(lib / "stool.glb", size=(0.4, 0.45, 0.4), tris=80)
    (lib / "Brick_diffuse.png").write_bytes(b"\x89PNG\r\n\x1a\nnot-a-real-png")
    (lib / "Brick_normal.png").write_bytes(b"\x89PNG\r\n\x1a\nnot-a-real-png")
    (lib / "Brick_rough.png").write_bytes(b"\x89PNG\r\n\x1a\nnot-a-real-png")
    (lib / "unrelated.txt").write_text("ignore me")
    store = AssetStore(tmp_path)
    report = ingest_directory(store, lib)
    assert report["models"] == 1
    assert report["material_sets"] == 1
    index = store.index()
    assert index["local:stool"]["tris"] == 80
    assert index["local:stool"]["dims_m"] == pytest.approx([0.4, 0.4, 0.45])
    maps = index["local:Brick"]["maps"]
    assert set(maps) == {"base_color", "normal", "roughness"}


def test_texture_set_regex_variants(tmp_path):
    from tee.assets.ingest import texture_sets

    paths = [
        tmp_path / "Wood_2k_BaseColor.png",
        tmp_path / "Wood_2k_nor_gl.png",
        tmp_path / "Wood_2k_Roughness.png",
        tmp_path / "Metal-metallic.jpg",
        tmp_path / "Metal-albedo.jpg",
        tmp_path / "lonely_diffuse.png",
    ]
    sets = texture_sets(paths)
    assert set(sets["Wood"]) == {"base_color", "normal", "roughness"}
    assert set(sets["Metal"]) == {"metallic", "base_color"}
    assert "lonely" not in sets


def test_unknown_material_category_fails_loud():
    # hard rule 6 (SI-2.4): an unknown category must not answer an empty
    # list that reads like "no materials exist"
    import pytest

    from tee.assets.materials import list_materials
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        list_materials("unobtainium")
    assert err.value.code == "unknown_category"
    assert "metal" in err.value.fix
