"""Phase 9.7: the render-free verification battery."""

from __future__ import annotations

from tee.app import TeeApp
from tee.assets.verify import verify_scene
from tee.kernel.adapter import FakeAdapter


def _app(tmp_path):
    return TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)


def _add(app, name, location, dims, **extra):
    props = {"location": location, "dims_m": dims, **extra}
    out = app.run_batch("fake", [{"op": "create", "kind": "object", "name": name, "props": props}])
    return out["created"][0]


def test_clean_scene_passes(tmp_path):
    app = _app(tmp_path)
    _add(app, "sofa", [0, 0, 0], [2.1, 0.9, 0.8], asset_class="sofa")
    _add(app, "chair", [2.5, 0, 0], [0.5, 0.5, 0.9], asset_class="chair")
    report = verify_scene(app, "fake")
    assert report["violations"] == []
    assert "no geometric conflicts" in report["summary"]
    assert report["render_warranted"] is False  # no visual question pending


def test_collision_detected_contact_tolerated(tmp_path):
    app = _app(tmp_path)
    _add(app, "a", [0, 0, 0], [1.0, 1.0, 1.0])
    _add(app, "b", [0.5, 0, 0], [1.0, 1.0, 1.0])  # 0.5 m overlap
    _add(app, "c", [1.999, 1.5, 0], [1.0, 1.0, 1.0])  # kissing contact with b at 1.5y? no - far
    report = verify_scene(app, "fake")
    collisions = [v for v in report["violations"] if v["check"] == "collision"]
    assert len(collisions) == 1
    assert collisions[0]["penetration_m"] >= 0.49
    assert "separate" in collisions[0]["fix"]


def test_floating_object_flagged(tmp_path):
    app = _app(tmp_path)
    _add(app, "floater", [0, 0, 0.8], [0.5, 0.5, 0.5])
    report = verify_scene(app, "fake")
    support = [v for v in report["violations"] if v["check"] == "support"]
    assert support and "floats" in support[0]["fix"]


def test_stacked_object_is_supported(tmp_path):
    app = _app(tmp_path)
    _add(app, "table", [0, 0, 0], [1.2, 0.8, 0.75], asset_class="table")
    _add(app, "lamp", [0, 0, 0.75], [0.2, 0.2, 0.4])
    report = verify_scene(app, "fake")
    assert not [v for v in report["violations"] if v["check"] == "support"]


def test_scale_sanity_from_asset_key(tmp_path):
    app = _app(tmp_path)
    _add(app, "minisofa", [0, 0, 0], [0.4, 0.18, 0.15], asset_key="polyhaven:tiny_sofa")
    report = verify_scene(app, "fake")
    sanity = [v for v in report["violations"] if v["check"] == "scale_sanity"]
    assert sanity and "envelope" in sanity[0]["fix"]


def test_room_clearances_flow_through(tmp_path):
    app = _app(tmp_path)
    _add(app, "chair", [0.5, 0.4, 0], [0.5, 0.5, 0.9], asset_class="chair")
    room = {
        "polygon": [[0, 0], [4, 0], [4, 3], [0, 3]],
        "doors": [{"id": "d1", "hinge": [0.05, 0.0], "width": 0.86}],
    }
    report = verify_scene(app, "fake", room=room)
    assert any(v["check"] == "door_swing_clear" for v in report["violations"])


def test_palette_check(tmp_path):
    app = _app(tmp_path)
    _add(app, "wall", [0, 0, 0], [4, 0.2, 2.6], base_color=[0.9, 0.1, 0.1])
    brief = [[70.0, 5.0, 15.0]]  # warm beige-ish brief
    report = verify_scene(app, "fake", style_palette=brief)
    palette = [v for v in report["violations"] if v["check"] == "palette"]
    assert palette and palette[0]["delta_e"] > 28
