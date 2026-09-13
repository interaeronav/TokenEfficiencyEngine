"""A78 benchmark cannot promote schemas, skips or escalation to live success."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "benchmarks" / "run_a78_lane_quality.py"
_SPEC = importlib.util.spec_from_file_location("a78_quality", _SCRIPT)
assert _SPEC and _SPEC.loader
bench = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bench)


def _task(task_id="bl_dimensions"):
    return next(t for t in bench.load_suite()["tasks"] if t["id"] == task_id)


def _record():
    return {
        "answer": {
            "ops": [{"op": "create", "kind": "cube"}],
            "verification": ["read actual geometry"],
            "claims": {"executed": False, "validated": False},
        },
        "escalated": False,
    }


def _evidence(task):
    expected = dict(task["expected"])
    if task["id"] == "fu_plate":
        expected.update({"bbox_min_mm": [20, 25, 0], "bbox_max_mm": [157, 108, 7]})
    if "volume_formula" in task:
        f = task["volume_formula"]
        expected["volume_mm3"] = (
            f["width"] * f["height"] - math.pi * (f["hole_diameter"] / 2) ** 2
        ) * f["depth"]
    return {
        "source": f"live_{task['adapter']}",
        "status": "executed",
        "observations": expected,
        "preservation": {"before": "fixed-fixture-hash", "after": "fixed-fixture-hash"},
    }


def test_json_success_is_not_model_task_success():
    task = _task()
    assert bench.schema_grade(_record()["answer"])["valid"]
    result = bench.grade(task, _record(), None)
    assert not result["success"]
    assert result["missing_evidence"]
    assert "live_execution" in result["failed"]


@pytest.mark.parametrize("status", ["skipped", "escalated", "failed", "timeout", "unavailable"])
def test_every_unfinished_outcome_fails_even_if_numbers_match(status):
    task = _task()
    ev = _evidence(task)
    ev["status"] = status
    assert not bench.grade(task, _record(), ev)["success"]


def test_client_escalation_cannot_count_as_local_success():
    task = _task()
    record = _record()
    record["escalated"] = True
    result = bench.grade(task, record, _evidence(task))
    assert not result["success"] and "no_escalation" in result["failed"]


@pytest.mark.parametrize("task_id", [t["id"] for t in bench.load_suite()["tasks"]])
def test_each_frozen_case_passes_independent_matching_measurements(task_id):
    task = _task(task_id)
    assert bench.grade(task, _record(), _evidence(task))["success"]


def test_millimetres_reported_as_metres_fail_regardless_of_unit_label():
    task = _task()
    ev = _evidence(task)
    ev["observations"]["dimensions_m"] = [137, 83, 41]
    ev["observations"]["unit"] = "metres"
    result = bench.grade(task, _record(), ev)
    assert not result["success"] and "dimensions_m" in result["failed"]


def test_wrong_hole_volume_cannot_pass_matching_bounding_box():
    task = _task("fu_hole")
    ev = _evidence(task)
    ev["observations"]["volume_mm3"] = 92 * 61 * 6.5
    assert not bench.grade(task, _record(), ev)["success"]


def test_correct_plate_size_at_the_wrong_origin_fails():
    task = _task("fu_plate")
    ev = _evidence(task)
    ev["observations"]["bbox_min_mm"] = [0, 0, 0]
    ev["observations"]["bbox_max_mm"] = [137, 83, 7]
    result = bench.grade(task, _record(), ev)
    assert not result["success"]
    assert "bbox_min_mm" in result["failed"]


def test_missing_or_changed_protected_state_fails():
    task = _task()
    for preservation in ({}, {"before": "", "after": ""}, {"before": "before", "after": "after"}):
        ev = _evidence(task)
        ev["preservation"] = preservation
        assert not bench.grade(task, _record(), ev)["success"]


def test_a_shim_report_cannot_become_live_evidence():
    task = _task()
    ev = _evidence(task)
    ev["source"] = "shim_blender"
    assert not bench.grade(task, _record(), ev)["success"]


@pytest.mark.parametrize("number", [float("nan"), float("inf"), True, None])
def test_nonfinite_and_boolean_measurements_fail(number):
    task = _task("bl_camera")
    ev = _evidence(task)
    ev["observations"]["lens_mm"] = number
    assert not bench.grade(task, _record(), ev)["success"]


def test_model_claiming_validation_before_execution_fails():
    task = _task()
    record = _record()
    record["answer"]["claims"]["validated"] = True
    assert not bench.grade(task, record, _evidence(task))["success"]


def test_model_abstention_is_preserved_as_failure():
    record = _record()
    record["answer"]["abstention"] = "cannot safely choose an ID"
    assert not bench.schema_grade(record["answer"])["valid"]


def test_generation_keeps_failure_and_stops_on_infrastructure_error(tmp_path, monkeypatch):
    import argparse

    calls = []

    def unavailable(*args, **kwargs):
        calls.append(kwargs["model"])
        raise bench.TeeError("llm_unreachable", "the explicit local endpoint is offline")

    monkeypatch.setattr(bench.local_llm, "complete", unavailable)
    args = argparse.Namespace(
        url="http://127.0.0.1:1/v1",
        model="local-test",
        fixtures=bench.FIXTURE,
        out=tmp_path,
        only=None,
        arm="baseline",
        max_tokens=500,
        timeout=1,
    )
    bench.generate(args)
    path = tmp_path / "bl_dimensions.json"
    first = path.read_bytes()
    assert len(calls) == 1
    assert "llm_unreachable" in first.decode()
    assert not (tmp_path / "bl_camera.json").exists()
    # A repeated invocation cannot replace the already recorded failure.
    bench.generate(args)
    assert path.read_bytes() == first


def test_resume_refuses_a_different_model_before_calling_it(tmp_path, monkeypatch):
    import argparse
    import json

    manifest = {
        "fixture_sha256": bench.digest(bench.FIXTURE.read_bytes()),
        "arm": "baseline",
        "model_requested": "frozen-model",
        "endpoint": "http://127.0.0.1:1/v1",
        "max_tokens": 500,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    args = argparse.Namespace(
        url=manifest["endpoint"],
        model="different-model",
        fixtures=bench.FIXTURE,
        out=tmp_path,
        only=None,
        arm="baseline",
        max_tokens=500,
        timeout=1,
    )
    called = []
    monkeypatch.setattr(bench.local_llm, "complete", lambda *a, **k: called.append(True))
    with pytest.raises(SystemExit, match="different frozen experiment"):
        bench.generate(args)
    assert called == []


def test_provider_usage_is_not_estimated_context_and_cache_is_not_added(tmp_path):
    import json

    record = {
        "usage_calls": [
            {
                "provider_usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 40,
                    "total_tokens": 240,
                    "prompt_tokens_details": {"cached_tokens": 150},
                }
            }
        ],
        "schema": {"valid": True},
        "error": None,
        "wall_seconds": 3,
        "estimated_context_tokens": 310,
        "estimated_answer_tokens": 80,
    }
    (tmp_path / "one.json").write_text(json.dumps(record))
    summary = bench.summarize_generation(tmp_path)
    assert summary["provider_reported_totals"]["total_tokens"] == 240
    assert summary["provider_cached_prompt_tokens"] == 150
    assert summary["estimated_context_tokens"] == 310
    assert summary["geometry_successes"] is None
