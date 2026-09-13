"""A80: learned ordering never becomes execution authority or a quality oracle."""

from __future__ import annotations

import json
import math

import pytest
from fixtures_llm import fake_llm_server
from test_llm_router import _by_model, _call, _cfg

from tee.kernel import shadow
from tee.kernel.errors import TeeError
from tee.kernel.machine import MachineLedger
from tee.llm import router


class Learning:
    def __init__(self, recommend=None):
        self.observations = []
        self.requests = []
        self.ranker = recommend

    def observe(self, **row):
        self.observations.append(row)

    def recommend(self, **request):
        self.requests.append(request)
        if self.ranker:
            return self.ranker(request["candidates"])
        return {"applied": False, "items": request["candidates"]}


@pytest.fixture(autouse=True)
def no_global_recorder():
    shadow.RECORDER.disable()
    yield
    shadow.RECORDER.disable()


def config(tmp_path, learning):
    return dict(_cfg("http://private-model.invalid/v1", tmp_path), _learning=learning)


def run(cfg, call, ledger=None, **kwargs):
    return router.route(
        "triage",
        call,
        cfg=cfg,
        ledger=ledger or MachineLedger(total_gb=128),
        input_pointer="private/input/must-not-be-retained",
        **kwargs,
    )


def accept(_cfg):
    return {"schema_valid": True}


def reverse(candidates):
    return {"applied": True, "items": list(reversed(candidates))}


def test_real_chore_validator_outcomes_and_default_response_shape(tmp_path):
    learning = Learning()
    with fake_llm_server(_by_model({"fake-dsflash", "fake-27b", "fake-35b"})) as (url, _):
        cfg = dict(_cfg(url, tmp_path), _learning=learning)
        result = run(cfg, _call)
    assert result["ok"]
    # These hops run `triage`, whose validator was MEASURED to accept 100% of
    # seeded wrong answers (chores.VERIFIER_COVERAGE, 2026-09-13). Its
    # ACCEPTANCE therefore carries no quality information and is stored
    # unlabelled; its REJECTION still does, because eps counts false accepts
    # and a rejection is a true catch. Hence [False, None], not [False, True].
    assert [row["success"] for row in learning.observations] == [False, None]
    assert {row["domain"] for row in learning.observations} == {"verified"}
    assert {row["context"] for row in learning.observations} == {"chore:triage"}
    assert set(result) == {"ok", "engine", "result", "hops", "pinned", "qos"}
    assert all(
        math.isfinite(row["elapsed_ms"]) and row["elapsed_ms"] > 0 for row in learning.observations
    )
    assert len({row["group_id"] for row in learning.observations}) == 1
    encoded = json.dumps(learning.observations)
    assert url not in encoded and "private/input" not in encoded and "diagnosis" not in encoded


@pytest.mark.parametrize(
    ("error", "expected", "category"),
    [
        ("llm_bad_shape", False, "completed"),
        ("llm_bad_json", False, "completed"),
        ("llm_unreachable", None, "unreachable"),
        ("trust_denied", None, "unknown"),
        ("llm_loading", None, "unknown"),
        ("unclassified_failure", None, "unknown"),
    ],
)
def test_only_known_validator_errors_are_negative_quality(tmp_path, error, expected, category):
    learning = Learning()

    def fail(_cfg):
        raise TeeError(error, "private error text must not be retained")

    result = run(config(tmp_path, learning), fail)
    assert not result["ok"]
    assert learning.observations
    assert all(
        row["success"] is expected and row["category"] == category for row in learning.observations
    )
    assert "private error text" not in json.dumps(learning.observations)


def test_empty_result_is_failure_and_each_hop_has_its_own_clock(tmp_path, monkeypatch):
    learning = Learning()
    ticks = iter([10.0, 10.007, 20.0, 20.013])
    monkeypatch.setattr(router.time, "perf_counter", lambda: next(ticks))
    attempts = iter([None, {"valid": True}])
    run(config(tmp_path, learning), lambda _cfg: next(attempts))
    assert [r["elapsed_ms"] for r in learning.observations] == pytest.approx([7, 13])
    # These hops run `triage`, whose validator was MEASURED to accept 100% of
    # seeded wrong answers (chores.VERIFIER_COVERAGE, 2026-09-13). Its
    # ACCEPTANCE therefore carries no quality information and is stored
    # unlabelled; its REJECTION still does, because eps counts false accepts
    # and a rejection is a true catch. Hence [False, None], not [False, True].
    assert [r["success"] for r in learning.observations] == [False, None]


def test_group_changes_per_route_and_code_or_engine_identity_changes_version(tmp_path):
    learning = Learning()
    cfg = config(tmp_path, learning)
    run(cfg, accept)
    initial = learning.observations[-1]
    run(cfg, accept)
    assert learning.observations[-1]["version"] == initial["version"]
    assert learning.observations[-1]["group_id"] != initial["group_id"]
    for key, value in [
        ("model", "replacement"),
        ("url", "http://other.invalid/v1"),
        ("adapters", "another-private-adapter"),
    ]:
        cfg["profiles"]["q14b"][key] = value
        run(cfg, accept)
        assert learning.observations[-1]["version"] != initial["version"]
        initial = learning.observations[-1]

    def changed_validator(_cfg):
        return {"different_contract": 1}

    run(cfg, changed_validator)
    assert learning.observations[-1]["version"] != initial["version"]
    assert "private-model" not in json.dumps(learning.observations)


@pytest.mark.parametrize("policy", ["static", "greedy"])
def test_applied_model_reorders_local_eligible_engines_and_marks_only_trace(tmp_path, policy):
    learning = Learning(reverse)
    shadow.RECORDER.enable(tmp_path / "shadow")
    ledger = MachineLedger(total_gb=128)
    result = run(config(tmp_path, learning), accept, ledger, policy=policy)
    assert result["engine"] == learning.requests[0]["candidates"][-1]["choice"]
    assert "learning" not in result
    trace = shadow.RECORDER.recent(1)[0]
    assert trace["actual"]["dispatch"].startswith(policy + ":")
    assert "learned:" in trace["actual"]["dispatch"]


@pytest.mark.parametrize("policy", ["static", "greedy"])
def test_pin_never_consults_recommendation(tmp_path, policy):
    learning = Learning(reverse)
    (tmp_path / "llm-profile.json").write_text(
        json.dumps(
            {
                "active": "q27b",
                "ready": True,
                "pinned": True,
            }
        )
    )
    result = run(config(tmp_path, learning), accept, policy=policy)
    assert result["engine"] == "q27b-bare" and result["pinned"]
    assert not learning.requests
    assert len(learning.observations) == 1


@pytest.mark.parametrize(
    "response",
    [
        None,
        {"applied": False},
        {"applied": 1, "items": []},
        {"applied": True, "items": []},
        {"applied": True, "items": [{}]},
    ],
)
def test_bad_or_abstaining_recommendations_keep_legacy_order(tmp_path, response):
    learning = Learning(lambda _: response)
    assert run(config(tmp_path, learning), accept)["engine"] == router.LADDER[0]


@pytest.mark.parametrize("damage", ["injection", "duplicate", "missing", "stale", "mutation"])
def test_recommendations_cannot_add_drop_duplicate_or_relabel_candidates(tmp_path, damage):
    def damaged(candidates):
        items = [dict(row) for row in reversed(candidates)]
        if damage == "injection":
            items[0]["choice"] = "paid-injected"
        elif damage == "duplicate":
            items[0] = items[1]
        elif damage == "missing":
            items.pop()
        elif damage == "stale":
            items[0]["version"] = "old"
        else:
            candidates[0]["choice"] = "paid-injected"
            items = candidates
        return {"applied": True, "items": items}

    learning = Learning(damaged)
    assert run(config(tmp_path, learning), accept)["engine"] == router.LADDER[0]


def test_paid_undeclared_disabled_and_memory_ineligible_candidates_are_excluded(
    tmp_path, monkeypatch
):
    learning = Learning(reverse)
    cfg = config(tmp_path, learning)
    cfg["profiles"]["q27b"]["paid"] = True
    cfg["profiles"]["dsflash"]["enabled"] = False
    specs = router.profiles.profiles(cfg)
    specs.pop("q35b")
    monkeypatch.setattr(router.profiles, "profiles", lambda _cfg: specs)
    result = run(cfg, accept, MachineLedger(total_gb=32))
    assert result["engine"] == "q14b+a2"
    assert not learning.requests  # Only one candidate; no speculative ranking.


def test_memory_eligibility_is_rechecked_after_ranking(tmp_path):
    ledger = MachineLedger(total_gb=128)

    def busy(candidates):
        ledger.register_job("owner-job", "reconstruct-odm")
        return reverse(candidates)

    learning = Learning(busy)
    seen = []

    def call(cfg):
        seen.append(cfg["_profile"])
        return {"valid": True}

    result = run(config(tmp_path, learning), call, ledger)
    assert result["ok"] and seen == ["q14b"]
    skipped = [row for row in learning.observations if row["category"] == "skipped"]
    assert skipped and all(row["success"] is None for row in skipped)


@pytest.mark.parametrize("change", ["paid", "capability", "disabled"])
def test_candidate_cannot_change_eligibility_after_recommendation(tmp_path, monkeypatch, change):
    cfg = config(tmp_path, None)
    specs = {name: dict(spec) for name, spec in router.ENGINES.items()}
    monkeypatch.setattr(router, "ENGINES", specs)

    def mutate(candidates):
        picked = candidates[-1]["choice"]
        profile = specs[picked]["profile"]
        if change == "capability":
            specs[picked]["capability"] = []
        elif change == "paid":
            cfg["profiles"][profile]["paid"] = True
        else:
            cfg["profiles"][profile]["enabled"] = False
        return reverse(candidates)

    learning = Learning(mutate)
    cfg["_learning"] = learning
    result = run(cfg, accept)
    excluded = learning.requests[0]["candidates"][-1]["choice"]
    assert result["engine"] != excluded
    if change != "paid":  # Changing paid also invalidates the version: legacy fallback.
        assert result["hops"][0]["engine"] == excluded
        assert "skipped" in result["hops"][0]


def test_missing_profile_and_swap_refusal_are_unknown_labels(tmp_path, monkeypatch):
    learning = Learning()
    cfg = config(tmp_path, learning)
    specs = router.profiles.profiles(cfg)
    specs.pop("dsflash")
    monkeypatch.setattr(router.profiles, "profiles", lambda _cfg: specs)
    run(cfg, lambda _cfg: None, MachineLedger(total_gb=32))
    skipped = [r for r in learning.observations if r["category"] == "skipped"]
    # q27b-bare left the ladder (rho = 1.00 with q27b-think, so it could
    # recover nothing); q35b is the other skipped rung now.
    assert {r["choice"] for r in skipped} >= {"dsflash", "q35b"}
    assert all(r["success"] is None for r in skipped)


def test_learning_service_failures_do_not_break_route(tmp_path):
    class Broken:
        def recommend(self, **_request):
            raise RuntimeError("offline store")

        def observe(self, **_row):
            raise RuntimeError("offline store")

    result = run(config(tmp_path, Broken()), accept)
    assert result["ok"] and result["engine"] == router.LADDER[0]


def test_real_service_persists_hop_labels_without_enabling_untrained_routing(tmp_path):
    from tee.learning.service import LearningService

    service = LearningService(tmp_path, {"auto_promote": False})
    cfg = config(tmp_path, service)
    outcomes = iter([None, {"schema_valid": True}])
    result = run(cfg, lambda _cfg: next(outcomes))
    assert result["engine"] == router.LADDER[1]
    rows = list(reversed(service.recent()))
    # These hops run `triage`, whose validator was MEASURED to accept 100% of
    # seeded wrong answers (chores.VERIFIER_COVERAGE, 2026-09-13). Its
    # ACCEPTANCE therefore carries no quality information and is stored
    # unlabelled; its REJECTION still does, because eps counts false accepts
    # and a rejection is a true catch. Hence [False, None], not [False, True].
    assert [row["success"] for row in rows] == [False, None]
    assert len({row["group_id"] for row in rows}) == 1
    service.close()
    reopened = LearningService(tmp_path)
    assert len(reopened.recent()) == 2
    assert (
        reopened.recommend(
            "verified",
            "chore:triage",
            [{"choice": row["choice"], "version": row["version"]} for row in rows],
        )["applied"]
        is False
    )
    reopened.close()


def test_identity_changed_during_recommendation_discards_the_order(tmp_path):
    cfg = config(tmp_path, None)

    def change_model(candidates):
        cfg["profiles"]["q35b"]["model"] = "new-unmeasured-model"
        return reverse(candidates)

    cfg["_learning"] = Learning(change_model)
    assert run(cfg, accept)["engine"] == router.LADDER[0]


def test_unknown_chore_text_never_contributes_a_retained_identifier(tmp_path):
    learning = Learning()
    for name in ("private user sentence / a prompt", "_run"):
        router.route(
            name,
            accept,
            cfg=config(tmp_path, learning),
            ledger=MachineLedger(total_gb=128),
            input_pointer="private input",
        )
    assert "private" not in json.dumps(learning.observations)
    assert {row["context"] for row in learning.observations} == {"chore:unknown"}
    assert len({row["version"] for row in learning.observations}) == 1
