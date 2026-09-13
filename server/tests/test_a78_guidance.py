"""Offline assistance must save a failed round trip without claiming success."""

from __future__ import annotations

import pytest

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError


class OfflineLane(FakeAdapter):
    def __init__(self):
        super().__init__()
        self.calls = []

    def probe(self):
        self.calls.append("probe")
        return False

    def guide(self, topic=None):
        return {"units": "mm", "topic": topic, "topics": ["part"]}

    def preflight(self, ops):
        if ops[0].get("kind") != "part":
            raise TeeError("bad_kind", "Expected part.", fix="Use kind='part'.")

    def snapshot(self):
        self.calls.append("snapshot")
        raise AssertionError("offline validation must never snapshot")


def test_guide_and_preflight_work_while_application_is_disconnected(tmp_path):
    lane = OfflineLane()
    app = TeeApp({"offline": lane}, tmp_path)
    guide = app.registry.call("lane_guide", {"adapter": "offline", "topic": "part"})
    assert guide["units"] == "mm" and guide["offline"] is True
    result = app.registry.call(
        "lane_preflight", {"adapter": "offline", "ops": [{"op": "create", "kind": "part"}]}
    )
    assert result["checked"] == "adapter syntax"
    assert result["live_state_checked"] is False
    assert lane.calls == []


def test_invalid_batch_fails_before_probe_or_checkpoint(tmp_path):
    lane = OfflineLane()
    app = TeeApp({"offline": lane}, tmp_path)
    with pytest.raises(TeeError, match="Expected part") as err:
        app.run_batch("offline", [{"op": "create", "kind": "invented"}])
    assert "No batch operation or checkpoint was applied" in err.value.fix
    assert lane.calls == []


def test_valid_syntax_still_requires_a_live_application(tmp_path):
    lane = OfflineLane()
    app = TeeApp({"offline": lane}, tmp_path)
    with pytest.raises(TeeError) as err:
        app.run_batch("offline", [{"op": "create", "kind": "part"}])
    assert err.value.code == "adapter_unavailable"
    assert lane.calls == ["probe"]


@pytest.mark.parametrize("ops", [None, [], ["create"], [{}], [{"op": "create", "props": []}]])
def test_bad_outer_shape_never_reaches_the_application(tmp_path, ops):
    lane = OfflineLane()
    app = TeeApp({"offline": lane}, tmp_path)
    with pytest.raises(TeeError) as err:
        app.run_batch("offline", ops)
    assert err.value.code == "bad_batch"
    assert lane.calls == []


def test_old_adapter_is_supported_but_validation_is_not_overstated(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, tmp_path)
    result = app.registry.call(
        "lane_preflight", {"adapter": "fake", "ops": [{"op": "create", "kind": "object"}]}
    )
    assert result["checked"] == "outer shape only"
    assert app.registry.call("lane_guide", {"adapter": "fake"})["detailed_contract"] is False
    assert app.run_batch("fake", [{"op": "create", "kind": "object"}])["applied"] == 1


def test_missing_lane_does_not_probe_other_lanes(tmp_path):
    lane = OfflineLane()
    app = TeeApp({"offline": lane}, tmp_path)
    with pytest.raises(TeeError) as err:
        app.registry.call("lane_guide", {"adapter": "missing"})
    assert err.value.code == "unknown_adapter"
    assert lane.calls == []
