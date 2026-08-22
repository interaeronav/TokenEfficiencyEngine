"""The job contract on the FakeEngine: one bounded call, compact report,
budget verdicts with exact fixes, cache hits, structured refusal."""

import numpy as np
import pytest
from PIL import Image

from voxkiln.engine import EngineUnavailable, FakeEngine, probe
from voxkiln.jobs import JobStore


@pytest.fixture()
def image(tmp_path):
    path = tmp_path / "input.png"
    rng = np.random.default_rng(0)
    Image.fromarray(rng.integers(0, 255, (32, 32, 3), dtype=np.uint8)).save(path)
    return path


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("VOXKILN_CACHE", str(tmp_path / "cache"))
    return JobStore(
        engine=FakeEngine(),
        out_dir=tmp_path / "out",
    )


def _params():
    return {"texture_size": 64, "target_faces": 2000}


def test_generate_returns_the_compact_report(store, image):
    report = store.generate(image, params=_params(), seed=7, timeout_s=60)
    assert report["state"] == "done"
    assert report["files"]["glb"].endswith(".glb")
    stats = report["stats"]
    assert stats["tris"] > 0 and stats["watertight"] is True
    prov = report["provenance"]
    assert prov["ai_generated"] is True
    assert prov["generator"] == "voxkiln"
    assert prov["seed"] == 7
    assert len(prov["input_image_sha256"]) == 64
    assert prov["upstream_commit"].startswith("75fbf01")
    assert report["verdict"]["accepted"] is True
    assert "mesh_hash" in report and "timings_s" in report


def test_budget_rejection_names_the_exact_fix(store, image):
    report = store.generate(image, params=_params(), budget={"max_tris": 10}, timeout_s=60)
    verdict = report["verdict"]
    assert verdict["accepted"] is False
    v = verdict["violations"][0]
    assert v["rule"] == "max_tris"
    assert "target_faces=10" in v["fix"]


def test_unknown_budget_key_fails_loud(store, image):
    with pytest.raises(ValueError, match="unknown budget keys"):
        store.generate(image, params=_params(), budget={"max_polys": 5}, timeout_s=60)


def test_cache_hit_skips_generation(store, image):
    first = store.generate(image, params=_params(), seed=1, timeout_s=60)
    assert "cache_hit" not in first
    ack = store.submit(image, params=_params(), seed=1)
    assert ack["cache_hit"] is True
    second = store.wait(ack["job_id"], timeout_s=5)
    assert second["cache_hit"] is True
    assert second["mesh_hash"] == first["mesh_hash"]


def test_different_seed_misses_cache(store, image):
    store.generate(image, params=_params(), seed=1, timeout_s=60)
    ack = store.submit(image, params=_params(), seed=2)
    assert ack["cache_hit"] is False
    store.wait(ack["job_id"], timeout_s=60)


def test_submit_ack_carries_estimates(store, image):
    ack = store.submit(image, params={**_params(), "pipeline_type": "512"}, seed=3)
    assert ack["est_seconds"] > 0
    assert ack["est_peak_mem_gb"] > 0
    store.wait(ack["job_id"], timeout_s=60)


def test_missing_image_fails_loud(store):
    with pytest.raises(FileNotFoundError):
        store.submit("no_such_image.png")


def test_no_backend_is_a_structured_refusal(tmp_path, image):
    # this container has neither CUDA nor MPS - the honest-degradation path
    assert probe()["backend"] is None
    bare = JobStore(out_dir=tmp_path / "o")
    with pytest.raises(EngineUnavailable) as exc:
        bare.submit(image)
    payload = exc.value.payload
    assert payload["error"] == "no_backend"
    assert payload["fix"]


def test_query_reports_state(store, image):
    report = store.generate(image, params=_params(), timeout_s=60)
    q = store.query(report["asset_id"])
    assert q["state"] == "done"
    assert q["stats"]["tris"] == report["stats"]["tris"]
