"""Phase 9.2/9.3: color science, four-band scale policy, faceted search,
import flow against the fake adapter."""

from __future__ import annotations

import pytest
from fixtures_assets import FakeBackend, build_glb, make_rows

from tee.app import TeeApp
from tee.assets import importer
from tee.assets.color import delta_e2000, kmeans_palette, name_rgb, srgb_to_lab
from tee.assets.envelopes import non_uniform_allowed, scale_policy
from tee.assets.search import AssetSearch
from tee.assets.store import AssetStore
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError

# -- CIEDE2000 against the Sharma 2005 reference pairs ---------------------

SHARMA_PAIRS = [
    ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
    ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
    ((50.0, 2.8361, -74.0200), (50.0, 0.0, -82.7485), 3.4412),
    ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
    ((50.0, 2.5, 0.0), (50.0, 3.2592, 0.3350), 1.0000),
]


@pytest.mark.parametrize(("lab1", "lab2", "expected"), SHARMA_PAIRS)
def test_ciede2000_reference(lab1, lab2, expected):
    assert delta_e2000(lab1, lab2) == pytest.approx(expected, abs=1e-3)
    assert delta_e2000(lab2, lab1) == pytest.approx(expected, abs=1e-3)


def test_color_names():
    assert name_rgb((190, 45, 45)) == "red"
    assert name_rgb((250, 250, 250)) == "white"
    assert name_rgb((60, 105, 175)) == "blue"


def test_kmeans_palette_two_clusters():
    pixels = [(200, 30, 30)] * 30 + [(30, 30, 200)] * 10
    palette = kmeans_palette(pixels, k=2)
    assert len(palette) == 2
    assert palette[0][1] == pytest.approx(0.75)
    # dominant cluster is the red one
    red_lab = srgb_to_lab((200, 30, 30))
    assert delta_e2000(palette[0][0], red_lab) < 5


# -- four-band scale policy ------------------------------------------------


def test_band_accept():
    verdict = scale_policy([2.1, 0.9, 0.8], asset_class="sofa")
    assert verdict["band"] == "accept"
    assert verdict["scale"] == 1.0


def test_band_fix_millimeters():
    verdict = scale_policy([2100, 900, 800], asset_class="sofa")
    assert verdict["band"] == "fix"
    assert verdict["scale"] == pytest.approx(0.001)
    assert verdict["fact"]["kind"] == "scale_fix"
    assert verdict["dims"] == pytest.approx([2.1, 0.9, 0.8])


def test_band_fix_inches():
    verdict = scale_policy([34.0, 1.8, 80.0], asset_class="door")
    assert verdict["band"] == "fix"
    assert verdict["scale"] == pytest.approx(0.0254)


def test_band_snap_door_into_opening():
    """Acceptance: a door asset auto-scales into the 0.9 m plan opening."""
    verdict = scale_policy([0.86, 0.045, 2.03], asset_class="door", target=[0.9, 0, 2.05])
    assert verdict["band"] == "snap"
    assert 1.0 < verdict["scale"] < 1.06
    assert verdict["fact"]["kind"] == "scale_snap"
    # scaled width lands within 10% of the opening
    assert abs(verdict["dims"][0] - 0.9) <= 0.09


def test_band_reject_tiny_sofa():
    """Acceptance: a 0.4 m 'sofa' is rejected with one line."""
    verdict = scale_policy([0.4, 0.18, 0.15], asset_class="sofa")
    assert verdict["band"] == "reject"
    assert "does not fit" in verdict["note"]
    assert "\n" not in verdict["note"].strip()


def test_non_uniform_gates():
    assert non_uniform_allowed("table", "x") is True
    assert non_uniform_allowed("door", "x") is False  # rigid class
    assert non_uniform_allowed("sofa", "x") is False
    assert non_uniform_allowed("unknown_thing", "x") is False


# -- faceted search --------------------------------------------------------


@pytest.fixture()
def store(tmp_path):
    return AssetStore(tmp_path)


def test_search_facets_and_rank(store):
    backend = FakeBackend(store, rows=make_rows())
    search = AssetSearch(store, {"fakesource": backend})
    out = search.search("chair seating", asset_class="model", license_filter="CC0-1.0")
    ids = [r["id"] for r in out["results"]["model"]]
    assert "fakesource:sofa1" in ids  # CC0 + tagged seating
    assert "fakesource:chair1" not in ids  # CC-BY filtered out
    out2 = search.search("chair", max_tris=500)
    ids2 = [r["id"] for r in out2["results"]["model"]]
    assert ids2 == ["fakesource:ncchair"]  # only the 100-tri one


def test_search_row_budget(store):
    rows = make_rows() * 10
    backend = FakeBackend(store, rows=rows)
    search = AssetSearch(store, {"fakesource": backend})
    out = search.search("chair sofa seating")
    assert all(len(bucket) <= 5 for bucket in out["results"].values())


def test_search_survives_backend_failure(store):
    class Broken(FakeBackend):
        id = "broken"

        def search(self, *a, **k):
            raise RuntimeError("backend down")

    search = AssetSearch(
        store, {"fakesource": FakeBackend(store, rows=make_rows()), "broken": Broken(store)}
    )
    out = search.search("chair")
    assert out["results"]
    assert any("broken" in e for e in out["backend_errors"])


# -- import flow (fake adapter + fake backend) -----------------------------


def _fake_download(monkeypatch, glb_path):
    data = glb_path.read_bytes()
    monkeypatch.setattr(importer, "fetch_bytes", lambda url, headers=None: data)


def test_import_caches_scales_and_verifies(tmp_path, monkeypatch):
    glb = build_glb(tmp_path / "dl.glb", size=(0.86, 2.03, 0.045), tris=100)
    _fake_download(monkeypatch, glb)
    store = AssetStore(tmp_path)
    backend = FakeBackend(store, rows=make_rows())
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    # dims from the fake backend row are used before any probe
    out = importer.import_asset(
        app,
        store,
        {"fakesource": backend},
        "fakesource:sofa1",
        adapter="fake",
        asset_class="sofa",
        location=[1.0, 2.0, 0.0],
    )
    assert out["ok"] and out["scale_band"] == "accept"
    assert store.entry("fakesource:sofa1") is not None  # cached
    assert out["created"]
    ent = app.cache("fake").get(out["created"][0])
    assert ent.summary["asset_key"] == "fakesource:sofa1"
    # second import: no network needed (fetch_bytes now poisoned to fail)
    monkeypatch.setattr(
        importer, "fetch_bytes", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
    )
    out2 = importer.import_asset(
        app, store, {"fakesource": backend}, "fakesource:sofa1", adapter="fake",
        asset_class="sofa",
    )
    assert out2["ok"]
    assert "already in the scene" in out2.get("note", "")


def test_import_blocks_nc_at_download(tmp_path, monkeypatch):
    glb = build_glb(tmp_path / "dl.glb", size=(0.5, 0.9, 0.5), tris=10)
    _fake_download(monkeypatch, glb)
    store = AssetStore(tmp_path)
    backend = FakeBackend(store, rows=make_rows())
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    with pytest.raises(TeeError) as err:
        importer.import_asset(
            app, store, {"fakesource": backend}, "fakesource:ncchair", adapter="fake"
        )
    assert err.value.code == "license_blocked"
    assert store.index() == {}


def test_import_rejects_bad_scale(tmp_path, monkeypatch):
    store = AssetStore(tmp_path)
    rows = make_rows()
    rows[0].dims_m = [0.4, 0.18, 0.15]  # miniature "sofa"
    backend = FakeBackend(store, rows=rows)
    glb = build_glb(tmp_path / "dl.glb", size=(0.4, 0.15, 0.18), tris=10)
    _fake_download(monkeypatch, glb)
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    with pytest.raises(TeeError) as err:
        importer.import_asset(
            app, store, {"fakesource": backend}, "fakesource:sofa1",
            adapter="fake", asset_class="sofa",
        )
    assert err.value.code == "asset_rejected"


def test_zip_slip_blocked(tmp_path):
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../evil.txt", "x")
    with pytest.raises(TeeError) as err:
        importer._unpack_zip(buf.getvalue(), "test:zip")
    assert err.value.code == "bad_archive"
