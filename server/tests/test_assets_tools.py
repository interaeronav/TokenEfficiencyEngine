"""Phase 9: as_* virtual tools registered and callable end-to-end through
the registry against the fake adapter."""

from __future__ import annotations

import pytest
from fixtures_assets import FakeBackend, make_rows

from tee.app import TeeApp
from tee.assets import tools as asset_tools
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError


@pytest.fixture()
def app(tmp_path, monkeypatch):
    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    # swap the real backends for the fake one before registration
    store_holder = {}

    def fake_build(store, config=None):
        store_holder["store"] = store
        return {"fakesource": FakeBackend(store, rows=make_rows())}

    monkeypatch.setattr(asset_tools, "build_backends", fake_build)
    asset_tools.register_asset_tools(application, tmp_path)
    return application


def test_tools_registered_and_searchable(app):
    hits = app.registry.search("asset search find")
    assert any(h["name"] == "as_search" for h in hits)
    names = app.registry.names()
    for expected in (
        "as_sources", "as_search", "as_import", "as_credits", "as_materials",
        "as_material", "as_generate", "as_style_brief", "as_sun", "as_place",
        "as_ingest", "as_photo_material",
    ):
        assert expected in names


def test_as_sources_declares_tos(app):
    out = app.registry.call("as_sources", {})
    row = out["backends"][0]
    assert "assets" in row and "site_tos" in row


def test_as_search_through_registry(app):
    out = app.registry.call("as_search", {"query": "sofa seating"})
    assert out["results"]["model"]
    assert len(out["results"]["model"]) <= 5


def test_as_material_mutates_and_records_provenance(app):
    created = app.run_batch("fake", [{"op": "create", "kind": "cube", "name": "Wall"}])
    entity = created["created"][0]
    out = app.registry.call("as_material", {"id": entity, "query": "brick", "adapter": "fake"})
    assert out["provenance"]["honesty"] == "measured"
    assert entity in out["modified"]
    assert "checkpoint" in out


def test_as_sun_computes_without_apply(app):
    out = app.registry.call(
        "as_sun",
        {"lat": 39.742476, "lon": -105.1786, "when": "2003-10-17T12:30:30-07:00"},
    )
    assert abs(out["azimuth_deg"] - 194.34) < 1.0
    assert out["hdri"]["band"]


def test_as_sun_apply_creates_light(app):
    out = app.registry.call(
        "as_sun",
        {
            "lat": 39.742476,
            "lon": -105.1786,
            "when": "2003-10-17T12:30:30-07:00",
            "apply": True,
            "adapter": "fake",
        },
    )
    assert out["created"]
    ent = app.cache("fake").get(out["created"][0])
    assert ent.summary["light_type"] == "SUN"


def test_as_place_refuses_apply_on_violation(app):
    room = {
        "polygon": [[0, 0], [4, 0], [4, 3], [0, 3]],
        "walls": [{"id": "south", "a": [0, 0], "b": [4, 0]}],
        "doors": [{"id": "d1", "hinge": [0.05, 0.0], "width": 0.86}],
    }
    created = app.run_batch(
        "fake", [{"op": "create", "kind": "chair", "name": "Chair"}]
    )
    plan = [
        {
            "name": "chair",
            "class": "chair",
            "dims": [0.5, 0.5, 0.9],
            "location": [0.5, 0.4],
            "id": created["created"][0],
        }
    ]
    out = app.registry.call("as_place", {"plan": plan, "room": room, "apply": True})
    assert out["applied"] is False
    assert any(v["rule"] == "door_swing_clear" for v in out["violations"])
    # clean position applies
    plan[0]["location"] = [2.0, 1.5]
    plan[0]["relax"] = ["back_to_wall"]
    out2 = app.registry.call("as_place", {"plan": plan, "room": room, "apply": True})
    assert out2["applied"] is True
    ent = app.cache("fake").get(created["created"][0])
    assert ent.summary["location"][:2] == [2.0, 1.5]


def test_as_generate_without_drivers_names_fix(app):
    with pytest.raises(TeeError) as err:
        app.registry.call("as_generate", {"prompt": "a chair"})
    assert err.value.code == "no_generators"
    assert "TEE_TRIPO_KEY" in (err.value.fix or "")


def test_as_credits_roundtrip(app, tmp_path):
    out = app.registry.call("as_credits", {"path": str(tmp_path / "CREDITS.md")})
    assert out["assets"] == 0
    assert (tmp_path / "CREDITS.md").exists()


def test_as_sheet_local_material(app, tmp_path):
    from PIL import Image

    lib = tmp_path / "lib"
    lib.mkdir()
    Image.new("RGB", (64, 64), (180, 60, 40)).save(lib / "Brick_diffuse.png")
    Image.new("RGB", (64, 64), (128, 128, 255)).save(lib / "Brick_normal.png")
    app.registry.call("as_ingest", {"directory": str(lib)})
    out = app.registry.call("as_sheet", {"assets": ["local:Brick"], "cell": 128})
    assert out["cells"] and out["tokens"] > 0
    from pathlib import Path

    assert Path(out["path"]).exists()


def test_as_sheet_no_thumbs_errors(app):
    with pytest.raises(TeeError) as err:
        app.registry.call("as_sheet", {"assets": ["fakesource:sofa1"]})
    assert err.value.code == "no_thumbnails"
