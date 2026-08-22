"""Phase 9.4/9.5: creation lanes (procedural, generation adapter, classical
photo-PBR) and context awareness (sun, style brief, placement rules)."""

from __future__ import annotations

import pytest

from tee.assets import materials
from tee.assets.context import (
    _avoid_terms,
    hdri_query,
    sun_ops,
    sun_position,
)
from tee.assets.generation import GenerationLane
from tee.assets.placement import solve_plan, validate_placement
from tee.kernel.errors import TeeError

# -- lane 0: procedural materials from measured data -----------------------


def test_material_lookup_measured_values():
    resolved = materials.material_props("aluminum")
    assert resolved["props"]["metallic"] == 1.0
    assert resolved["props"]["base_color"] == pytest.approx([0.916, 0.923, 0.924])
    prov = resolved["provenance"]
    assert prov["dataset"] == "physicallybased.info"
    assert prov["license"] == "CC0-1.0"
    assert prov["honesty"] == "measured"
    assert prov["density_kg_m3"] == 2700


def test_material_unknown_names_alternatives():
    with pytest.raises(TeeError) as err:
        materials.find_material("unobtanium")
    assert err.value.code == "unknown_material"
    assert "as_materials" in (err.value.fix or "")


def test_material_assign_ops():
    ops, provenance = materials.assign_ops("e1", "brick")
    assert ops[0]["op"] == "assign_material"
    assert ops[0]["id"] == "e1"
    assert provenance["kind"] == "material_provenance"


def test_materials_list_compact():
    rows = materials.list_materials("metal")
    assert rows and all("name" in r for r in rows)
    assert any(r["name"] == "Gold" for r in rows)


# -- generation lane contract ----------------------------------------------


class FakeDriver:
    id = "fakegen"

    def __init__(self, paid=True, polls_needed=2, fail=False):
        self.paid = paid
        self.polls = 0
        self.polls_needed = polls_needed
        self.fail = fail
        self.submitted = None

    def estimate(self, kind, options):
        return {"cost_usd": 0.30, "note": "test"}

    def submit(self, kind, prompt, options):
        self.submitted = (kind, prompt)
        return "task-1"

    def poll(self, task_id):
        self.polls += 1
        if self.fail:
            return {"state": "failed", "error": "boom"}
        if self.polls >= self.polls_needed:
            return {"state": "done", "result": {"model_url": "https://x/model.glb"}}
        return {"state": "running"}


def _lane(driver):
    return GenerationLane({"fakegen": driver}, sleep=lambda s: None)


def test_generation_cost_gate():
    lane = _lane(FakeDriver(paid=True))
    with pytest.raises(TeeError) as err:
        lane.generate("fakegen", "text_to_model", "a chair")
    assert err.value.code == "cost_confirmation_required"
    assert "0.3" in err.value.message


def test_generation_wait_polls_server_side():
    driver = FakeDriver(paid=True, polls_needed=3)
    out = _lane(driver).generate("fakegen", "text_to_model", "a chair", confirm_cost=True)
    assert out["ok"] and driver.polls == 3  # polling happened HERE, not in context
    assert out["model_url"].endswith(".glb")
    prov = out["provenance"]
    assert prov["kind"] == "ai_generated"
    assert "not copyrightable" in prov["copyright_note"]


def test_generation_failure_is_one_message():
    lane = _lane(FakeDriver(fail=True))
    with pytest.raises(TeeError) as err:
        lane.generate("fakegen", "text_to_model", "x", confirm_cost=True)
    assert err.value.code == "generation_failed"


def test_free_driver_needs_no_confirmation():
    driver = FakeDriver(paid=False, polls_needed=1)
    out = _lane(driver).generate("fakegen", "text_to_model", "a chair")
    assert out["ok"]


# -- lane 2: classical photo-PBR -------------------------------------------


def test_photo_pbr_maps(tmp_path):
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    from tee.assets.photo_pbr import derive_maps, make_tileable, rectify

    rng = np.random.default_rng(7)
    img = (rng.uniform(60, 200, (128, 128, 3))).astype("uint8")
    src = tmp_path / "wall.png"
    cv2.imwrite(str(src), img)

    rect = rectify(
        src,
        [[10, 10], [118, 14], [116, 120], [8, 116]],
        tmp_path / "rect.png",
        width_m=2.0,
        height_m=2.0,
        px_per_m=64,
    )
    assert rect["px"] == [128, 128]

    maps = derive_maps(tmp_path / "rect.png", tmp_path / "maps", surface="masonry")
    assert maps["metallic"] == 0.0
    assert "estimated" in maps["honesty"]
    normal = cv2.imread(maps["normal"])
    assert normal is not None and normal.shape[:2] == (128, 128)

    tiled = make_tileable(tmp_path / "rect.png", tmp_path / "tile.png")
    tile = cv2.imread(tiled["path"])
    # wrapped edges must now match closely (tileable)
    seam = np.abs(tile[:, 0].astype(int) - tile[:, -1].astype(int)).mean()
    raw = cv2.imread(str(tmp_path / "rect.png"))
    raw_seam = np.abs(raw[:, 0].astype(int) - raw[:, -1].astype(int)).mean()
    assert seam <= raw_seam


# -- sun position (NREL SPA reference; acceptance: within 1 degree) --------


def test_sun_position_matches_nrel_reference():
    out = sun_position(39.742476, -105.1786, "2003-10-17T12:30:30-07:00")
    assert abs(out["azimuth_deg"] - 194.34) <= 1.0
    assert abs(out["elevation_deg"] - 39.888) <= 1.0


def test_sun_position_timezone_and_night():
    out = sun_position(-26.2041, 28.0473, "2026-06-21T02:00:00", tz="Africa/Johannesburg")
    assert out["elevation_deg"] < 0
    assert "night" in out.get("note", "")


def test_sun_ops_shape():
    ops = sun_ops("fake", {"azimuth_deg": 180.0, "elevation_deg": 45.0})
    props = ops[0]["props"]
    assert props["light_type"] == "SUN"
    assert props["rotation_euler"][0] == pytest.approx(0.7854, abs=1e-3)


def test_hdri_bands():
    assert hdri_query(50)["band"] == "midday"
    assert hdri_query(5)["band"] == "sunrise-sunset"
    assert hdri_query(-10)["band"] == "night"


def test_avoid_terms():
    text = "We want natural light. No marble please, avoid chrome, don't want clutter."
    terms = _avoid_terms(text)
    assert "marble" in terms and "chrome" in terms and "clutter" in terms


# -- placement solve + validate --------------------------------------------

ROOM = {
    "polygon": [[0, 0], [4, 0], [4, 3], [0, 3]],
    "walls": [
        {"id": "south", "a": [0, 0], "b": [4, 0]},
        {"id": "north", "a": [4, 3], "b": [0, 3]},
    ],
    "doors": [
        {"id": "d1", "hinge": [0.05, 0.0], "width": 0.86, "swing_start_deg": 0.0},
        {"id": "d2", "hinge": [3.95, 3.0], "width": 0.86, "swing_start_deg": 180.0},
    ],
}


def test_solve_against_wall():
    placements = solve_plan(
        [
            {
                "name": "sofa",
                "class": "sofa",
                "dims": [2.1, 0.9, 0.8],
                "anchor": "south",
                "offset": 2.0,
            }
        ],
        ROOM,
    )
    x, y = placements[0]["location"]
    assert y == pytest.approx(0.47, abs=0.01)  # depth/2 + margin off the wall
    assert x == pytest.approx(2.0, abs=0.01)


def test_validator_catches_blocked_door_swing():
    """Acceptance: blocked door swing (code severity)."""
    placements = solve_plan(
        [{"name": "chair", "class": "chair", "dims": [0.5, 0.5, 0.9], "location": [0.5, 0.4]}],
        ROOM,
    )
    report = validate_placement(placements, ROOM)
    rules = {v["rule"] for v in report["violations"]}
    assert "door_swing_clear" in rules
    swing = next(v for v in report["violations"] if v["rule"] == "door_swing_clear")
    assert swing["severity"] == "code"


def test_validator_catches_narrow_corridor():
    """Acceptance: sub-760 mm corridor between the two doors."""
    placements = [
        {
            "name": "wardrobe1",
            "class": "wardrobe",
            "dims": [2.6, 1.3, 2.0],
            "location": [1.35, 1.5],
            "rotation_deg": 0,
            "relax": [],
        },
        {
            "name": "wardrobe2",
            "class": "wardrobe",
            "dims": [1.0, 1.25, 2.0],
            "location": [3.6, 1.5],
            "rotation_deg": 0,
            "relax": [],
        },
    ]
    report = validate_placement(placements, ROOM)
    passage = [v for v in report["violations"] if v["rule"] == "passage_min"]
    assert passage, report
    assert any("clear path" in v["fix"] for v in passage)


def test_validator_clean_room_reports_check_count():
    placements = solve_plan(
        [
            {
                "name": "sofa",
                "class": "sofa",
                "dims": [2.1, 0.9, 0.8],
                "anchor": "north",
                "offset": 2.0,
            }
        ],
        ROOM,
    )
    report = validate_placement(placements, ROOM)
    assert report["violations"] == []
    assert "no placement conflicts" in report["summary"]
    assert report["checked"] > 0


def test_work_triangle_trap():
    placements = [
        {
            "name": "sink",
            "class": "sink",
            "dims": [0.6, 0.5, 0.9],
            "location": [0.4, 2.6],
            "rotation_deg": 0,
            "relax": [],
        },
        {
            "name": "stove",
            "class": "stove",
            "dims": [0.76, 0.65, 0.91],
            "location": [3.6, 2.6],
            "rotation_deg": 0,
            "relax": [],
        },
        {
            "name": "fridge",
            "class": "refrigerator",
            "dims": [0.75, 0.7, 1.75],
            "location": [3.6, 0.6],
            "rotation_deg": 0,
            "relax": [],
        },
    ]
    report = validate_placement(placements, ROOM)
    tri = [v for v in report["violations"] if v["rule"] == "work_triangle"]
    assert tri and tri[0]["severity"] == "guideline"


def test_guideline_relaxes_with_note_code_never():
    placements = [
        {
            "name": "sofa",
            "class": "sofa",
            "dims": [2.0, 0.9, 0.8],
            "location": [2.0, 1.5],
            "rotation_deg": 0,
            "relax": ["back_to_wall"],
        },
    ]
    report = validate_placement(placements, ROOM)
    assert not any(v["rule"] == "back_to_wall" for v in report["violations"])
    assert any(v["rule"] == "back_to_wall" for v in report.get("relaxed", []))
    # code rules ignore relax
    placements = [
        {
            "name": "chair",
            "class": "chair",
            "dims": [0.5, 0.5, 0.9],
            "location": [0.5, 0.4],
            "rotation_deg": 0,
            "relax": ["door_swing_clear"],
        },
    ]
    report = validate_placement(placements, ROOM)
    assert any(v["rule"] == "door_swing_clear" for v in report["violations"])


# -- local GPU probe: backends, not just CUDA --------------------------------


class _FakeCuda:
    def __init__(self, available: bool):
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def get_device_name(self, index: int) -> str:
        return "FakeGPU"

    def get_device_properties(self, index: int):
        class _P:
            total_memory = 24 * 2**30

        return _P()


class _FakeMps:
    def __init__(self, available: bool):
        self._available = available

    def is_available(self) -> bool:
        return self._available


class _FakeTorch:
    def __init__(self, cuda: bool, mps: bool):
        self.cuda = _FakeCuda(cuda)
        self.backends = type("B", (), {"mps": _FakeMps(mps)})()


def _with_torch(monkeypatch, torch_module):
    import sys

    monkeypatch.setitem(sys.modules, "torch", torch_module)


def test_probe_reports_cuda_with_all_three_lanes(monkeypatch):
    from tee.assets import generation

    _with_torch(monkeypatch, _FakeTorch(cuda=True, mps=False))
    out = generation.probe_local_gpu()
    assert out["available"] is True
    assert out["backend"] == "cuda"
    assert out["lanes"] == [1, 2, 3]
    assert generation.torch_device() == "cuda"


def test_probe_enables_the_diffusion_lanes_on_apple_silicon(monkeypatch):
    """The diffusion lanes are plain diffusers and run on MPS. Lane 3 on
    MPS depends on voxkiln (Phase 13 removed the nvdiffrast/cumesh CUDA
    lock): absent -> lanes 1-2 plus an install hint; present -> lane 3
    joins the list."""
    from tee.assets import gen_voxkiln, generation

    _with_torch(monkeypatch, _FakeTorch(cuda=False, mps=True))

    monkeypatch.setattr(gen_voxkiln, "voxkiln_available", lambda: False)
    out = generation.probe_local_gpu()
    assert out["available"] is True
    assert out["backend"] == "mps"
    assert out["lanes"] == [1, 2]
    assert "voxkiln" in out["note"]
    assert generation.torch_device() == "mps"

    monkeypatch.setattr(gen_voxkiln, "voxkiln_available", lambda: True)
    out = generation.probe_local_gpu()
    assert out["lanes"] == [1, 2, 3]
    assert "note" not in out


def test_probe_refuses_cpu_only_torch_with_a_reason(monkeypatch):
    from tee.assets import generation

    _with_torch(monkeypatch, _FakeTorch(cuda=False, mps=False))
    out = generation.probe_local_gpu()
    assert out["available"] is False
    assert out["backend"] == "cpu"
    assert "too slow" in out["fix"]


def test_probe_without_torch_names_both_accelerators(monkeypatch):
    import builtins

    from tee.assets import generation

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "torch":
            raise ImportError("no torch")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    out = generation.probe_local_gpu()
    assert out["available"] is False
    assert "MPS" in out["fix"] and "CUDA" in out["fix"]
