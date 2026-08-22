"""The voxkiln lane-3 driver: contract tests over an injected stub store
(the TEE server venv never carries torch/voxkiln - the fake carries the
contract, per the project's adapter-fake pattern)."""

import pytest

from tee.assets.gen_voxkiln import VoxkilnDriver
from tee.assets.generation import GenerationLane
from tee.kernel.errors import TeeError


class StubStore:
    """Mimics voxkiln.jobs.JobStore: instant-done jobs with the report
    shape the real product returns (mirrors voxkiln's own test suite)."""

    def __init__(self):
        self.submitted = []
        self.state = "done"

    def submit(self, image_path, params=None, budget=None, seed=0):
        self.submitted.append(
            {"image_path": image_path, "params": params, "budget": budget, "seed": seed}
        )
        return {"job_id": "vk-test1", "cache_hit": False, "est_seconds": 210}

    def query(self, job_id):
        if self.state != "done":
            return {"job_id": job_id, "state": self.state}
        return {
            "job_id": job_id,
            "state": "done",
            "asset_id": job_id,
            "files": {"glb": f"/out/{job_id}.glb"},
            "stats": {"tris": 1234, "watertight": True, "bbox": [1, 1, 1]},
            "repairs": [{"op": "fill_holes", "loops_filled": 2}],
            "verdict": {"accepted": True, "violations": []},
            "provenance": {
                "generator": "voxkiln",
                "model_revision": "abc123",
                "seed": 7,
                "input_image_sha256": "f" * 64,
                "ai_generated": True,
            },
            "mesh_hash": "deadbeef",
        }


@pytest.fixture()
def lane():
    return GenerationLane({"voxkiln": VoxkilnDriver(store=StubStore())}, sleep=lambda _s: None)


def test_generate_returns_report_with_driver_provenance(lane):
    out = lane.generate("voxkiln", "image_to_model", "/tmp/concept.png")
    assert out["ok"] is True
    assert out["stats"]["tris"] == 1234
    assert out["repairs"][0]["op"] == "fill_holes"
    # the driver's provenance (model revision, seed) wins over the lane's
    prov = out["provenance"]
    assert prov["model_revision"] == "abc123"
    assert prov["seed"] == 7
    assert prov["ai_generated"] is True
    # ... while lane fields absent from the driver's manifest still land
    assert prov["task_kind"] == "image_to_model"
    assert "copyright_note" in prov


def test_unpaid_no_cost_gate(lane):
    # no confirm_cost needed - voxkiln is local and free
    out = lane.generate("voxkiln", "image_to_model", "/tmp/concept.png", confirm_cost=False)
    assert out["ok"] is True


def test_options_map_to_params_budget_seed():
    store = StubStore()
    lane = GenerationLane({"voxkiln": VoxkilnDriver(store=store)}, sleep=lambda _s: None)
    lane.generate(
        "voxkiln",
        "image_to_model",
        "/tmp/c.png",
        options={
            "pipeline_type": "512",
            "target_faces": 90_000,
            "budget": {"max_tris": 100_000},
            "seed": 42,
        },
    )
    sub = store.submitted[0]
    assert sub["params"] == {"pipeline_type": "512", "target_faces": 90_000}
    assert sub["budget"] == {"max_tris": 100_000}
    assert sub["seed"] == 42


def test_text_kind_fails_with_image_route(lane):
    with pytest.raises(TeeError) as exc:
        lane.generate("voxkiln", "text_to_model", "a red chair")
    assert exc.value.code == "image_required"
    assert "concept image" in exc.value.fix


def test_failed_job_becomes_lane_error():
    class FailingStore(StubStore):
        def query(self, job_id):
            return {
                "job_id": job_id,
                "state": "failed",
                "error": "no_backend",
                "message": "no device can run the generation pipeline here",
                "fix": "install voxkiln[model] on Apple Silicon or CUDA hardware",
            }

    lane = GenerationLane({"voxkiln": VoxkilnDriver(store=FailingStore())}, sleep=lambda _s: None)
    with pytest.raises(TeeError) as exc:
        lane.generate("voxkiln", "image_to_model", "/tmp/c.png")
    assert exc.value.code == "generation_failed"
    assert "install voxkiln[model]" in str(exc.value)


def test_estimate_is_free():
    driver = VoxkilnDriver(store=StubStore())
    est = driver.estimate("image_to_model", {})
    assert est["cost_usd"] == 0


def test_build_drivers_puts_voxkiln_first(monkeypatch):
    import tee.assets.gen_voxkiln as vk_mod
    import tee.assets.generation as gen_mod

    monkeypatch.setattr(vk_mod, "voxkiln_available", lambda: True)
    monkeypatch.setenv("TEE_TRIPO_KEY", "k")
    drivers = gen_mod.build_drivers()
    ids = list(drivers)
    assert ids[0] == "voxkiln"
    assert "tripo" in ids
