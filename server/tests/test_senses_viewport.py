"""A47 — the viewport and active-camera senses.

The asymmetry that prompted this: Unreal shipped `ue_look` (viewport ->
local model -> text) in 3.7; Blender never got an equivalent, so a blind
host driving Blender could mutate the scene and never see the result -
the owner watched DeepSeek struggle to get a view of the Blender it was
running. `sense_viewport` answers about what the camera already shows;
`sense_camera` lets the model AIM first.
"""

from __future__ import annotations

import pytest

from tee import senses
from tee.kernel import local_vlm
from tee.kernel.errors import TeeError

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64  # a plausible tiny payload


class FakeBlender:
    def __init__(self):
        self.look_calls = []

    def capture(self, view, max_bytes):
        return JPEG

    def capture_look(self, max_bytes, *, target, azimuth_deg, elevation_deg, distance):
        self.look_calls.append((target, azimuth_deg, elevation_deg, distance))
        return JPEG


@pytest.fixture(autouse=True)
def fake_vlm(monkeypatch):
    monkeypatch.setattr(local_vlm, "describe", lambda data, q, **kw: "a fake description")
    senses.configure({})
    yield
    senses.configure({})


def test_viewport_answers_in_text_and_charges_no_image_tokens():
    r = senses.viewport({"question": "what is visible?"}, adapters={"blender": FakeBlender()})
    assert r["answer"] == "a fake description"
    assert r["cost"]["host_tokens_for_the_image"] == 0
    assert r["cost"]["off_machine_calls"] == 0
    assert "never entered your context" in r["note"]


def test_viewport_refuses_with_no_dcc_connected():
    with pytest.raises(TeeError) as e:
        senses.viewport({}, adapters={})
    assert e.value.code == "sense_no_adapter"


def test_viewport_names_the_connected_adapters_on_a_typo():
    with pytest.raises(TeeError) as e:
        senses.viewport({"adapter": "blendr"}, adapters={"blender": FakeBlender()})
    assert "blender" in e.value.fix


def test_a_broken_capture_is_a_named_refusal_not_a_traceback():
    class Broken:
        def capture(self, view, max_bytes):
            raise RuntimeError("render exploded")

    with pytest.raises(TeeError) as e:
        senses.viewport({}, adapters={"blender": Broken()})
    assert e.value.code == "sense_capture_failed"


def test_camera_aims_where_it_was_told():
    fake = FakeBlender()
    r = senses.camera(
        {"target": "arm-pad-L", "azimuth_deg": 200, "elevation_deg": 15, "distance": 3.0},
        adapters={"blender": fake},
    )
    assert fake.look_calls == [("arm-pad-L", 200.0, 15.0, 3.0)]
    assert r["aimed_at"] == "arm-pad-L"
    assert "left exactly as found" in r["note"]


def test_camera_is_blender_only_and_points_unreal_at_ue_look():
    with pytest.raises(TeeError) as e:
        senses.camera({}, adapters={"unreal": object()})
    assert "ue_look" in e.value.fix


def test_camera_refuses_an_adapter_without_the_aimed_capture():
    class Old:
        def capture(self, view, max_bytes):
            return JPEG

    with pytest.raises(TeeError) as e:
        senses.camera({}, adapters={"blender": Old()})
    assert "predates" in e.value.message


def test_camera_context_travels_into_the_question(monkeypatch):
    seen = {}

    def spy(data, q, **kw):
        seen["q"] = q
        return "ok"

    monkeypatch.setattr(local_vlm, "describe", spy)
    senses.camera(
        {"context": "part of chair AURA-X", "question": "which part?"},
        adapters={"blender": FakeBlender()},
    )
    assert seen["q"].startswith("Context: part of chair AURA-X")


def test_another_users_config_overrides_endpoint_model_and_facts(monkeypatch):
    seen = {}

    def spy(data, q, **kw):
        seen.update(kw)
        return "ok"

    monkeypatch.setattr(local_vlm, "describe", spy)
    senses.configure(
        {
            "vision_url": "http://10.0.0.7:8000/v1",
            "vision_model": "llava-7b",
            "vision_footprint_gb": 4.2,
            "vision_evicts": [],
        }
    )
    r = senses.viewport({}, adapters={"blender": FakeBlender()})
    assert seen["url"] == "http://10.0.0.7:8000/v1"
    assert seen["model"] == "llava-7b"
    assert "llava-7b" in r["provided_by"] and "4.2 GB" in r["provided_by"]
    assert "swap_note" not in r  # their machine declared no eviction


def test_both_tools_are_read_tier():
    from tee.kernel import trust

    assert trust.capability_for("sense_viewport") == "read-scene"
    assert trust.capability_for("sense_camera") == "read-scene"


def test_a_blind_host_can_find_the_viewport(tmp_path):
    from tee.app import TeeApp
    from tee.senses import register_sense_tools

    app = TeeApp({}, project_root=tmp_path)
    register_sense_tools(app, tmp_path)
    top = [
        i["name"]
        for i in app.registry.search("see the blender viewport, look at the scene")["items"]
    ][:3]
    assert "sense_viewport" in top or "sense_camera" in top
