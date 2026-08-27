"""[assets-embed] and [assets-gen]: the logic offline, the models under -m ml.

The model-backed tests are marked `ml` rather than `dcc` - they need multi-
gigabyte weights, not a DCC - so a normal run never pulls them.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tee.assets.embed import MODEL_LICENSE, SiglipTextEmbedder, evaluate, row_key, row_text


def row(rid, name, tags, cls="model"):
    return SimpleNamespace(id=rid, name=name, tags=tags, asset_class=cls, source="test")


# -- embedder logic (no model) -----------------------------------------------


def test_row_text_and_key_are_stable():
    r = row("sofa", "Grey sofa", ["couch", "seating"])
    assert row_text(r) == "Grey sofa couch seating model"
    assert row_key(r) == "test:sofa"


def test_embedder_is_lazy_and_never_loads_without_a_query():
    embedder = SiglipTextEmbedder()
    assert embedder._model is None
    assert embedder.score_rows("", [row("a", "A", [])]) == {}
    assert embedder.score_rows("chair", []) == {}
    assert embedder._model is None, "scoring nothing must not load the model"


def test_search_scores_semantically_once_per_rank_not_per_row():
    """An embedding model wants one batched pass; calling it inside the sort
    comparator would re-run it O(n log n) times."""
    from tee.assets.search import AssetSearch

    calls: list[str] = []

    class CountingEmbedder:
        def score_rows(self, query, rows):
            calls.append(query)
            return {row_key(r): 1.0 if r.id == "stool" else 0.0 for r in rows}

    rows = [row("sofa", "Sofa", []), row("stool", "Stool", []), row("lamp", "Lamp", [])]
    search = AssetSearch(store=None, backends={}, embedder=CountingEmbedder())
    ranked = search._rank(rows, "seating", None)
    assert len(calls) == 1, f"embedder called {len(calls)} times"
    assert ranked[0].id == "stool"


def test_a_broken_embedder_never_breaks_search():
    from tee.assets.search import AssetSearch

    class Exploding:
        def score_rows(self, query, rows):
            raise RuntimeError("model went away")

    rows = [row("a", "Alpha chair", []), row("b", "Beta", [])]
    search = AssetSearch(store=None, backends={}, embedder=Exploding())
    ranked = search._rank(rows, "chair", None)
    assert ranked[0].id == "a"  # keyword ranking still applies


def test_keyword_still_outranks_semantic_similarity():
    """Semantic similarity breaks ties and rescues synonyms; it must not
    override a literal name match."""
    from tee.assets.search import AssetSearch

    class AlwaysOne:
        def score_rows(self, query, rows):
            return {row_key(r): 1.0 if r.id == "other" else 0.0 for r in rows}

    rows = [row("exact", "chair", []), row("other", "stool", [])]
    search = AssetSearch(store=None, backends={}, embedder=AlwaysOne())
    assert search._rank(rows, "chair", None)[0].id == "exact"


# -- local diffusion driver logic (no model) ---------------------------------


def test_local_driver_is_free_and_image_only():
    from tee.assets.gen_local import LocalDiffusionDriver

    driver = LocalDiffusionDriver("/tmp/tee-gen-test")
    assert driver.paid is False
    assert driver.estimate("image", {})["cost_usd"] == 0.0
    with pytest.raises(ValueError) as err:
        driver.submit("3d", "a crate", {})
    assert "hosted driver or a CUDA machine" in str(err.value)


def test_uniform_output_is_rejected_not_saved():
    """fp16 on MPS returns NaNs, which cast to a flat black frame. Without
    this the driver reports state 'done' with a black PNG - silent, plausible,
    and only visible to a human who opens the file."""
    from PIL import Image

    from tee.assets.gen_local import _reject_degenerate

    _reject_degenerate(Image.linear_gradient("L").convert("RGB"), "mps")
    with pytest.raises(RuntimeError) as err:
        _reject_degenerate(Image.new("RGB", (8, 8), (0, 0, 0)), "mps")
    assert "uniform image" in str(err.value)
    assert "dtype" in str(err.value)


# -- model-backed (marked) ----------------------------------------------------


@pytest.mark.ml
def test_siglip_beats_keyword_ranking_on_synonym_queries(tmp_path):
    pool = [
        row("sofa", "Grey fabric sofa", ["couch", "living room"]),
        row("armchair", "Leather armchair", ["chair", "lounge"]),
        row("stool", "Oak bar stool", ["seat", "kitchen"]),
        row("lamp", "Brass floor lamp", ["lighting", "standing"]),
        row("chandelier", "Crystal chandelier", ["ceiling", "lighting"]),
        row("table", "Oak dining table", ["dining", "wood"]),
        row("rug", "Persian rug", ["carpet", "floor"]),
        row("fridge", "Steel refrigerator", ["kitchen", "appliance"]),
    ]
    cases = [
        {
            "query": "seating",
            "rows": pool,
            "relevant": ["test:sofa", "test:armchair", "test:stool"],
        },
        {
            "query": "something to light the room",
            "rows": pool,
            "relevant": ["test:lamp", "test:chandelier"],
        },
        {"query": "soft floor covering", "rows": pool, "relevant": ["test:rug"]},
        {"query": "cold food storage", "rows": pool, "relevant": ["test:fridge"]},
    ]
    embedder = SiglipTextEmbedder(cache_dir=tmp_path / "cache")
    report = evaluate(embedder, cases)
    assert report["license"] == MODEL_LICENSE == "Apache-2.0"
    assert report["semantic_mrr"] > report["keyword_mrr"], report
    # the on-disk cache means the second pass touches no model at all
    assert any(tmp_path.joinpath("cache").rglob("*.json"))


@pytest.mark.ml
def test_local_diffusion_generates_a_real_image(tmp_path):
    from PIL import Image

    from tee.assets.gen_local import LocalDiffusionDriver

    driver = LocalDiffusionDriver(tmp_path)
    task = driver.submit(
        "image", "a weathered wooden crate on concrete", {"steps": 8, "size": 512, "seed": 7}
    )
    result = driver.poll(task)
    assert result["state"] == "done"
    payload = result["result"]
    assert payload["license"] == "Apache-2.0"
    assert payload["device"] in ("mps", "cuda", "cpu")
    image = Image.open(payload["files"][0])
    assert image.size == (512, 512)
    low, high = image.convert("L").getextrema()
    assert high > low, "generated a uniform image"


# -- tileable SDXL driver logic (no model) -----------------------------------


def test_tileable_driver_is_free_and_image_only():
    from tee.assets.gen_tileable import TileableSdxlDriver

    driver = TileableSdxlDriver("/tmp/tee-tile-test")
    assert driver.paid is False
    assert driver.estimate("image", {})["cost_usd"] == 0.0
    with pytest.raises(ValueError) as err:
        driver.submit("3d", "a crate", {})
    assert "voxkiln or a hosted driver" in str(err.value)


def test_seam_ratio_separates_tileable_from_seamed():
    """A wrapped gradient tiles (ratio ~1); a linear gradient has a hard wrap
    seam (ratio >> threshold). The metric must tell them apart or the
    'tileable' verdict is decoration."""
    import numpy as np
    from PIL import Image

    from tee.assets.gen_tileable import SEAM_RATIO_TILEABLE, seam_ratio

    x = np.arange(64, dtype=np.float32)
    wrapped = (127.5 - 127.5 * np.cos(2 * np.pi * x / 64)).astype(np.uint8)
    tileable = Image.fromarray(np.tile(wrapped, (64, 1))).convert("RGB")
    seamed = Image.fromarray(np.tile((x * 4).astype(np.uint8), (64, 1))).convert("RGB")
    assert seam_ratio(tileable) <= SEAM_RATIO_TILEABLE
    assert seam_ratio(seamed) > SEAM_RATIO_TILEABLE


def test_make_convs_circular_patches_padded_convs_only():
    torch = pytest.importorskip("torch")

    from tee.assets.gen_tileable import make_convs_circular

    net = torch.nn.Sequential(
        torch.nn.Conv2d(3, 8, kernel_size=3, padding=1),
        torch.nn.Conv2d(8, 8, kernel_size=1),
        torch.nn.Sequential(torch.nn.Conv2d(8, 3, kernel_size=3, padding=1)),
    )
    assert make_convs_circular(net) == 2
    modes = [m.padding_mode for m in net.modules() if isinstance(m, torch.nn.Conv2d)]
    assert modes == ["circular", "zeros", "circular"]
    # a circularly padded conv on a wrapped signal stays wrap-consistent
    x = torch.randn(1, 3, 8, 8)
    y = net[0](x)
    y_rolled = net[0](torch.roll(x, shifts=3, dims=-1))
    assert torch.allclose(torch.roll(y, shifts=3, dims=-1), y_rolled, atol=1e-5)


# -- marigold refinement wiring (no model) -----------------------------------


def test_photo_material_falls_back_classical_when_marigold_unavailable(tmp_path, monkeypatch):
    """refine='auto' must degrade to the classical maps when the GPU lane
    raises; refine='marigold' must fail loud with the fix instead."""
    from PIL import Image

    from tee.app import TeeApp
    from tee.assets import photo_pbr_gpu
    from tee.assets.tools import register_asset_tools
    from tee.kernel.adapter import FakeAdapter
    from tee.kernel.errors import TeeError

    def unavailable(*a, **k):
        raise TeeError("marigold_missing", "no marigold here", fix="install it")

    monkeypatch.setattr(photo_pbr_gpu, "derive_maps_marigold", unavailable)
    photo = tmp_path / "wall.png"
    Image.linear_gradient("L").convert("RGB").save(photo)
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_asset_tools(app, tmp_path, extract_store=None)

    maps = app.registry.call("as_photo_material", {"photo": str(photo)})
    assert "estimated (classical)" in maps["honesty"]

    with pytest.raises(TeeError) as err:
        app.registry.call("as_photo_material", {"photo": str(photo), "refine": "marigold"})
    assert "no marigold here" in str(err.value)
