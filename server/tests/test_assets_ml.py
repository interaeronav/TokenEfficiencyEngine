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
