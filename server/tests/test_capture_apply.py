"""T5 on fakes (A42 acceptance): the owner's decision drives everything -
keep-design records and mutates nothing, accept-as-built moves the scene
entity through the checkpointed batch path (and the checkpoint really
rolls back), staged lanes refuse loudly, and every decision lands in the
paper trail."""

from __future__ import annotations

import json

import pytest
from test_capture_deviate import _fake_cc

from tee.app import TeeApp
from tee.capture.tools import register_capture_tools
from tee.extract.tools import register_extract_tools
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError


@pytest.fixture
def app_with_report(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    store, _ = register_extract_tools(app, project)
    cc = _fake_cc(tmp_path)
    app.config.capture = {"cloudcompare": cc["cloudcompare"]}
    register_capture_tools(app, project, extract_store=store)
    batch = app.run_batch(
        "fake",
        [{"op": "create", "kind": "wall", "name": "north_wall", "props": {"location": [0, 0, 0]}}],
    )
    entity_id = batch["created"][0]
    app.registry.call(
        "capture_deviate",
        {"source": str(cc["_src"]), "target": str(cc["_dst"]), "phrase": "off"},
    )
    return app, entity_id


def test_accept_moves_checkpoints_and_logs(app_with_report):
    app, entity = app_with_report
    out = app.registry.call(
        "capture_apply",
        {"deviation": "d1", "decision": "accept-as-built", "entity": entity},
    )
    (applied,) = out["applied"]
    assert applied["location"][2] == pytest.approx(0.038, abs=0.0005)
    assert applied["checkpoint"]
    log_lines = (app.project_root / ".tee").rglob("decisions.jsonl")
    (log,) = list(log_lines)
    entry = json.loads(log.read_text().splitlines()[-1])
    assert entry["decision"] == "accept-as-built" and entry["applied"][0]["entity"] == entity

    # the checkpoint is real: rolling back restores the design position
    app.rollback("fake", applied["checkpoint"])
    assert app.cache("fake").get(entity).summary["location"] == [0, 0, 0]
    app.shutdown()


def test_keep_design_records_and_mutates_nothing(app_with_report):
    app, entity = app_with_report
    out = app.registry.call("capture_apply", {"deviation": "d2", "decision": "keep-design"})
    assert out["applied"] == [] and "nothing applied" in out["note"]
    assert app.cache("fake").get(entity).summary["location"] == [0, 0, 0]
    app.shutdown()


def test_refusals_name_their_fixes(app_with_report):
    app, _entity = app_with_report
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_apply", {"deviation": "d1", "decision": "auto-fix"})
    assert excinfo.value.code == "capture_apply_bad_decision"
    assert "owner decides" in excinfo.value.fix

    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_apply", {"deviation": "d9", "decision": "keep-design"})
    assert excinfo.value.code == "capture_unknown_deviation"

    with pytest.raises(TeeError) as excinfo:
        app.registry.call("capture_apply", {"deviation": "d1", "decision": "accept-as-built"})
    assert excinfo.value.code == "capture_apply_needs_entity"

    for lane in ("fabrication", "unreal"):
        with pytest.raises(TeeError) as excinfo:
            app.registry.call(
                "capture_apply",
                {"deviation": "d1", "decision": "accept-as-built", "lanes": [lane]},
            )
        assert excinfo.value.code == "capture_apply_staged"

    with pytest.raises(TeeError) as excinfo:
        app.registry.call(
            "capture_apply",
            {"deviation": "d1", "decision": "accept-as-built", "lanes": ["gimp"]},
        )
    assert excinfo.value.code == "capture_apply_unknown_lane"
    app.shutdown()
