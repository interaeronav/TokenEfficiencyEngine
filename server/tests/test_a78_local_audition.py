"""A78: measure the requested local model and the budget actually sent."""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any

import pytest
from fixtures_llm import fake_llm_server

from tee.engines import audition, table
from tee.kernel.errors import TeeError
from tee.llm import chores, profiles

REPLY = json.dumps(
    {
        "diagnosis": "The signature is not in the evidence.",
        "fix": "Inspect the installed API signature before changing the argument.",
        "confidence": "needs_verification",
    }
)


@pytest.fixture(autouse=True)
def clear_probe_cache() -> None:
    chores._probe_cache.clear()
    yield
    chores._probe_cache.clear()


def local_cfg(url: str, state_dir: Path | None = None) -> dict[str, Any]:
    cfg = {
        "_profile": "q27b",
        "profiles": {"q27b": {"url": url, "model": "fake-27b", "adapters": ""}},
    }
    if state_dir is not None:
        cfg["_state_dir"] = str(state_dir)
    return cfg


def measured_row(url: str, count: int = 768) -> dict[str, Any]:
    return {
        "url": url,
        "model": "fake-27b",
        "adapters": None,
        "measured_at": time.time(),
        "min_chore_tokens": count,
        "floor": {"min_chore_tokens": count, "budget_mode": "exact-wire"},
    }


def test_audition_uses_requested_local_model_and_preserves_paid_pin(tmp_path: Path) -> None:
    state = {"active": "qmax", "ready": True, "pinned": True}
    state_path = tmp_path / profiles.STATE_FILE
    state_path.write_text(json.dumps(state))
    before_state = state_path.read_bytes()
    cfg = {
        "_state_dir": str(tmp_path),
        "url": "http://127.0.0.1:1/v1",
        "model": "fake-14b",
        "adapters": "/do/not/attach/14b-adapter",
        "profiles": {"qmax": {"url": "http://127.0.0.1:1/v1", "model": "paid-model", "paid": True}},
    }
    before_cfg = copy.deepcopy(cfg)
    with fake_llm_server([REPLY]) as (url, calls):
        row = audition.audition(cfg, engine="q27b-bare", url=url, model="fake-27b", samples=1)
    assert row["model"] == "fake-27b" and row["url"] == url
    assert row["verified_rate"] == 1
    assert row["adapters"] is None
    assert all(call["model"] == "fake-27b" and "adapters" not in call for call in calls)
    assert [call["max_tokens"] for call in calls] == [256, 256, *audition.TOKEN_RUNGS]
    assert row["floor"]["budget_mode"] == "exact-wire"
    assert row["floor"]["min_chore_tokens"] == 64
    assert row["floor"]["bound"] == "at-or-below"
    assert cfg == before_cfg
    assert state_path.read_bytes() == before_state
    assert profiles.resolve(cfg)["paid"] is True


def test_candidate_does_not_inherit_an_unrelated_loading_state(tmp_path: Path) -> None:
    state = {"active": "qmax", "ready": False, "since": time.time(), "eta_s": 90}
    (tmp_path / profiles.STATE_FILE).write_text(json.dumps(state))
    cfg = {"_state_dir": str(tmp_path), "profiles": {"qmax": {"model": "paid", "paid": True}}}
    candidate = audition._candidate_cfg(cfg, engine="q27b-bare", url="http://local/v1", model="m")
    assert profiles.resolve(candidate)["ready"] is True
    assert json.loads((tmp_path / profiles.STATE_FILE).read_text()) == state


def test_direct_audition_refuses_a_paid_model_before_any_chore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = {"profiles": {"qmax": {"model": "paid-model", "paid": True}}}

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("a paid candidate reached the chore")

    monkeypatch.setattr(audition, "_timed", forbidden)
    with pytest.raises(TeeError) as exc:
        audition.audition(cfg, engine="q27b-bare", url="http://local/v1", model="paid-model")
    assert exc.value.code == "eng_paid_refused"


def test_candidate_keeps_only_its_own_declared_adapter() -> None:
    cfg = {
        "url": "http://local/v1",
        "model": "fake-14b",
        "adapters": "/adapter/14b",
    }
    same = audition._candidate_cfg(cfg, engine="q14b+a2", url=cfg["url"], model="fake-14b")
    other = audition._candidate_cfg(cfg, engine="q27b-bare", url=cfg["url"], model="fake-27b")
    assert profiles.resolve(same)["adapters"] == "/adapter/14b"
    assert profiles.resolve(other)["adapters"] is None


@pytest.mark.parametrize("url,model", [("", "fake"), ("http://local/v1", ""), (" / ", " ")])
def test_blank_candidate_cannot_fall_back_to_owner_endpoint(url: str, model: str) -> None:
    cfg = {
        "url": "http://owner-paid/v1",
        "model": "paid-model",
        "profiles": {"qmax": {"model": "paid-model", "paid": True}},
    }
    with pytest.raises(TeeError) as exc:
        audition._candidate_cfg(cfg, engine="q27b-bare", url=url, model=model)
    assert exc.value.code == "eng_needs_endpoint"


def test_paid_name_is_checked_after_whitespace_normalization() -> None:
    cfg = {"profiles": {"qmax": {"model": "paid-model", "paid": True}}}
    with pytest.raises(TeeError) as exc:
        audition._candidate_cfg(
            cfg, engine="q27b-bare", url="http://local/v1", model=" paid-model "
        )
    assert exc.value.code == "eng_paid_refused"


def test_direct_floor_helper_cannot_use_paid_chore_grants(monkeypatch: pytest.MonkeyPatch) -> None:
    from tee.kernel import trust

    cfg = {
        "_profile": "qmax",
        "profiles": {"qmax": {"model": "paid-model", "paid": True}},
        "_grants": trust.Grants(granted=frozenset({"call-paid-engine"})),
        "_consent": True,
    }

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("a paid floor probe reached the chore transport")

    monkeypatch.setattr(chores, "_run", forbidden)
    with pytest.raises(TeeError) as exc:
        audition._chore(cfg, max_tokens=64)
    assert exc.value.code == "eng_paid_refused"


def test_floor_failure_is_observed_at_the_requested_wire_budget() -> None:
    def answer(request: dict[str, Any]) -> str:
        return REPLY if request["max_tokens"] >= 128 else "{}"

    with fake_llm_server(answer) as (url, calls):
        row = audition.token_floor(local_cfg(url))
    assert [call["max_tokens"] for call in calls] == [1024, 512, 384, 256, 192, 128, 96]
    assert row["min_chore_tokens"] == 128
    assert row["first_failure"] == 96


@pytest.mark.parametrize(
    "count,requested,expected", [(768, 220, 768), (64, 160, 160), (64, 1200, 1200)]
)
def test_normal_chore_uses_matching_adopted_floor(
    tmp_path: Path, count: int, requested: int, expected: int
) -> None:
    with fake_llm_server([REPLY]) as (url, calls):
        table.save_measured(tmp_path, {"q27b-bare": measured_row(url, count)})
        chores._run(
            "Use the supplied evidence.",
            "The installed signature is not shown.",
            refine="local",
            cfg=local_cfg(url, tmp_path),
            max_tokens=requested,
            validate=lambda value: value,
        )
    assert calls[0]["max_tokens"] == expected


@pytest.mark.parametrize(
    "change",
    [
        {"model": "different-model"},
        {"url": "http://other/v1"},
        {"adapters": "/other-adapter"},
        {"paid": True},
        {"measured_at": time.time() - 31 * 86400},
        {"floor": {"min_chore_tokens": 768}},
        {"min_chore_tokens": True},
        {"min_chore_tokens": -4},
        {"measured_at": "invalid"},
        {"measured_at": float("nan")},
    ],
)
def test_other_or_unverified_measurements_cannot_change_budget(
    tmp_path: Path, change: dict[str, Any]
) -> None:
    url = "http://local/v1"
    table.save_measured(tmp_path, {"q27b-bare": {**measured_row(url), **change}})
    assert table.matching_floors(tmp_path, profiles.resolve(local_cfg(url)), thinking=False) == {}


def test_endpoint_trailing_slash_does_not_invalidate_measurement(tmp_path: Path) -> None:
    table.save_measured(tmp_path, {"q27b-bare": measured_row("http://local/v1/")})
    matched = table.matching_floors(
        tmp_path, profiles.resolve(local_cfg("http://local/v1")), thinking=False
    )
    assert matched["q27b-bare"]["min_chore_tokens"] == 768


def test_local_measurement_cannot_override_paid_profile_budget(tmp_path: Path) -> None:
    url = "http://local/v1"
    table.save_measured(tmp_path, {"q27b-bare": measured_row(url)})
    resolved = {**profiles.resolve(local_cfg(url)), "paid": True}
    assert table.matching_floors(tmp_path, resolved, thinking=False) == {}


def test_schema_failure_reports_one_failed_shape_without_hidden_retry() -> None:
    with (
        fake_llm_server(['{"diagnosis":"missing fix and confidence"}']) as (url, calls),
        pytest.raises(TeeError) as exc,
    ):
        chores.triage("failure", refine="local", cfg=local_cfg(url))
    assert exc.value.code == "llm_bad_shape"
    assert "twice" not in str(exc.value)
    assert len(calls) == 1
