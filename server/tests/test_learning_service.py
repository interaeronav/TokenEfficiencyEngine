"""Local learning must earn influence using later, separate, current evidence."""

from __future__ import annotations

import json
import multiprocessing
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from tee.kernel.errors import TeeError
from tee.learning import LearningService, model
from tee.learning import service as module

CANDIDATES = [{"choice": "bad", "version": "v1"}, {"choice": "good", "version": "v1"}]


def observation(service, **changes):
    values = {
        "domain": "execution",
        "context": "fixture",
        "choice": "good",
        "version": "v1",
        "success": True,
        "elapsed_ms": 100,
    }
    return service.observe(**(values | changes))


def populate(service, count=80, start=0, domain="execution", **changes):
    for index in range(start, start + count):
        assert observation(
            service,
            **(
                {
                    "domain": domain,
                    "choice": "good" if index % 2 else "bad",
                    "success": bool(index % 2),
                    "group_id": f"task_{index}",
                }
                | changes
            ),
        )


def recommend(service, candidates=None, domain="execution"):
    return service.recommend(domain, "fixture", candidates or CANDIDATES)


def sql(service, statement, parameters=()):
    with sqlite3.connect(service.path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(statement, parameters)]


def _write_in_process(root, start_event, results):
    service = LearningService(root)
    start_event.wait(5)
    count = sum(observation(service) is not None for _ in range(20))
    service.close()
    results.put(count)


@pytest.fixture
def learner(tmp_path, monkeypatch):
    # Explicit evaluation tests do not race the separately tested automatic cadence.
    monkeypatch.setattr(module, "EVALUATE_EVERY", 1_000_000)
    instance = LearningService(tmp_path)
    yield instance
    instance.close()


def promote(service, domain="execution"):
    report = service.evaluate()["domains"][domain]
    assert report["promoted"], report
    return report


def test_cold_read_methods_and_disabled_collection_do_not_create_files(tmp_path):
    service = LearningService(tmp_path)
    assert service.status()["events"] == 0
    assert service.recent() == []
    assert recommend(service)["reason"] == "untrained"
    assert not service.evaluate()["evaluated"]
    assert not (tmp_path / ".tee").exists()
    disabled = LearningService(tmp_path, {"enabled": False})
    assert observation(disabled) is None
    assert recommend(disabled)["reason"] == "disabled"
    with pytest.raises(TeeError):
        disabled.control("resume")
    assert not (tmp_path / ".tee").exists()
    service.close()
    assert observation(service) is None
    assert recommend(service)["reason"] == "closed"


@pytest.mark.parametrize("config", [{"enabled": "false"}, {"auto_promote": 1}, [], False])
def test_malformed_config_disables_honestly_even_with_existing_state(tmp_path, config):
    good = LearningService(tmp_path)
    assert observation(good)
    good.close()
    service = LearningService(tmp_path, config)
    assert observation(service) is None
    status = service.status()
    assert not status["enabled"] and status["health"] == "invalid_config"
    assert status["events"] == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"context": "../private/file"},
        {"choice": "secret\ncredential"},
        {"version": "é"},
        {"context": "x" * 97},
        {"group_id": "https://private"},
        {"elapsed_ms": float("nan")},
        {"elapsed_ms": float("inf")},
        {"elapsed_ms": -1},
        {"elapsed_ms": True},
        {"tokens": 1.5},
        {"tokens": True},
        {"success": 1},
        {"domain": "user_secret"},
        {"category": "secret_error"},
    ],
)
def test_invalid_observations_fail_open_without_storing_or_echoing_payload(tmp_path, changes):
    service = LearningService(tmp_path)
    assert observation(service, **changes) is None
    assert service.status()["health"] == "observation_error"
    assert not service.path.exists()
    assert recommend(service)["reason"] == "unhealthy"
    assert observation(service)
    assert service.status()["health"] == "ok"
    service.close()


@pytest.mark.parametrize("category", sorted(module.UNLABELLED))
def test_unknown_or_unexecuted_outcomes_never_become_training_labels(learner, category):
    assert observation(learner, success=True, category=category)
    event = learner.recent()[0]
    assert event["success"] is None
    assert learner.status()["domains"]["execution"]["trainable_count"] == 0


def test_persistence_project_isolation_and_single_reported_feedback(learner, tmp_path):
    original = observation(learner, success=False, tokens=12)
    assert original.startswith("e_")
    reported = learner.feedback(original, True)
    assert reported["domain"] == "reported"
    with pytest.raises(TeeError) as duplicate:
        learner.feedback(original, False)
    assert duplicate.value.code == "learning_duplicate_feedback"
    with pytest.raises(TeeError):
        learner.feedback(reported["event_id"], False)
    events = learner.recent()
    assert events[0]["success"] is True and events[0]["source"] == "feedback"
    assert events[1]["success"] is False and events[1]["source"] == "runtime"
    assert events[0]["group_id"] == events[1]["group_id"]
    events[0]["choice"] = "changed"
    assert learner.recent()[0]["choice"] == "good"
    learner.close()
    reopened = LearningService(tmp_path)
    assert reopened.recent()[1]["event_id"] == original
    other = LearningService(tmp_path / "other_project")
    assert not other.recent()
    with pytest.raises(TeeError):
        other.feedback(original, True)
    assert not other.recent()
    reopened.close()
    other.close()


def test_two_instances_serialize_writes_and_feedback_without_duplicates(learner, tmp_path):
    original = observation(learner)
    second = LearningService(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(populate, instance, 24) for instance in (learner, second)]
        for future in futures:
            future.result()
        futures = [
            executor.submit(instance.feedback, original, True) for instance in (learner, second)
        ]
        outcomes = []
        for future in futures:
            try:
                outcomes.append(future.result())
            except TeeError as exc:
                outcomes.append(exc.code)
    assert sum(isinstance(value, dict) for value in outcomes) == 1
    assert "learning_duplicate_feedback" in outcomes
    assert learner.status()["events"] == 50
    second.close()


def test_independent_processes_commit_observations_to_the_same_project(learner, tmp_path):
    assert observation(learner)
    context = multiprocessing.get_context("spawn")
    start, results = context.Event(), context.Queue()
    processes = [
        context.Process(target=_write_in_process, args=(tmp_path, start, results)) for _ in range(2)
    ]
    for process in processes:
        process.start()
    start.set()
    try:
        assert sorted(results.get(timeout=10) for _ in processes) == [20, 20]
        for process in processes:
            process.join(timeout=10)
            assert process.exitcode == 0
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        results.close()
    assert learner.status()["events"] == 41


def test_real_model_promotes_only_training_prefix_and_survives_reopen(learner, tmp_path):
    populate(learner)
    report = promote(learner)
    assert (report["train"], report["holdout"]) == (64, 16)
    assert report["train_through_seq"] < report["holdout_from_seq"]
    assert report["candidate"]["brier"] < report["baseline"]["brier"] - 0.01
    snapshot = sql(learner, "SELECT * FROM snapshots")[0]
    learned = json.loads(snapshot["model_json"])
    assert learned["trained_rows"] == 64
    assert snapshot["through_seq"] == report["train_through_seq"]
    ranking = recommend(learner)
    assert ranking["applied"]
    assert [item["choice"] for item in ranking["items"]] == ["good", "bad"]
    assert not ranking["policy_speed_improvement_measured"]
    assert CANDIDATES[0]["choice"] == "bad"
    learner.close()
    restored = LearningService(tmp_path)
    assert recommend(restored) == ranking
    restored.close()


def test_evaluations_use_future_groups_without_reusing_holdout(learner):
    populate(learner)
    first = promote(learner)
    assert not learner.evaluate()["evaluated"]
    populate(learner, 15, start=80)
    assert not learner.evaluate()["evaluated"]
    populate(learner, 1, start=95)
    second = learner.evaluate()["domains"]["execution"]
    assert second["evaluated"]
    assert second["holdout_from_seq"] > first["holdout_through_seq"]
    assert second["train_through_seq"] < second["holdout_from_seq"]
    assert second["incumbent"]["count"] == second["candidate"]["count"] == 16


def test_interleaved_group_is_purged_from_train_and_late_old_group_is_not_holdout(learner):
    populate(learner, 80)
    # Repeating task_0 beyond the nominal split makes it span both regions.
    assert observation(learner, group_id="task_0")
    report = learner.evaluate()["domains"]["execution"]
    assert not report["evaluated"] and report["train"] == 63
    populate(learner, 2, start=80)
    first = promote(learner)
    # Old task IDs cannot supply the next held-out data, even with new rows.
    populate(learner, 30)
    assert not learner.evaluate()["evaluated"]
    populate(learner, 16, start=200)
    next_report = learner.evaluate()["domains"]["execution"]
    assert next_report["holdout_from_seq"] > first["holdout_through_seq"]


def test_domains_and_current_versions_require_full_candidate_evidence(learner):
    populate(learner)
    promote(learner)
    assert not recommend(learner, domain="verified")["applied"]
    partial = [{"choice": "good", "version": "v1"}, {"choice": "bad", "version": "v2"}]
    assert recommend(learner, partial)["items"] == partial
    assert not recommend(learner, partial)["applied"]
    assert observation(learner, choice="bad", version="v2")
    assert recommend(learner, partial)["reason"] == "uncovered_candidate"
    populate(learner, domain="verified")
    promote(learner, "verified")
    assert recommend(learner, domain="verified")["applied"]
    snapshots = sql(learner, "SELECT domain,model_json FROM snapshots")
    assert all(json.loads(row["model_json"])["domain"] == row["domain"] for row in snapshots)


@pytest.mark.parametrize("target", ["snapshot", "candidate"])
def test_stale_evidence_abstains_even_with_unchanged_version(learner, target):
    populate(learner)
    promote(learner)
    if target == "snapshot":
        sql(learner, "UPDATE snapshots SET created_ms=created_ms-?", (module.MAX_AGE_MS + 1,))
    else:
        sql(
            learner,
            "UPDATE events SET created_ms=created_ms-? WHERE choice='bad'",
            (module.MAX_AGE_MS + 1,),
        )
    answer = recommend(learner)
    assert not answer["applied"] and answer["items"] == CANDIDATES
    assert answer["reason"] == "stale_or_missing_evidence"


def test_auto_promote_disabled_still_measures_candidate(learner):
    learner.auto_promote = False
    populate(learner)
    report = learner.evaluate()["domains"]["execution"]
    assert report["evaluated"] and not report["promoted"]
    assert report["reasons"] == ["auto_promote_disabled"]
    assert report["candidate"]["brier"] < report["baseline"]["brier"]
    assert learner.status()["snapshots"] == 0


@pytest.mark.parametrize(
    "metric,value,reason",
    [
        ("brier", 0.25, "no_reliability_gain"),
        ("cost_log_mae", 0.05, "cost_regression"),
    ],
)
def test_promotion_rejects_unimproved_reliability_or_cost(
    learner, monkeypatch, metric, value, reason
):
    populate(learner)
    actual = model.evaluate

    def worse(candidate, rows):
        return actual(candidate, rows) | {metric: value}

    monkeypatch.setattr(model, "evaluate", worse)
    result = learner.evaluate()["domains"]["execution"]
    assert reason in result["reasons"] and not result["promoted"]
    assert not learner.status()["snapshots"]


def test_incumbent_regression_is_checked_on_identical_unseen_rows(learner, monkeypatch):
    populate(learner)
    promote(learner)
    populate(learner, 16, start=80)
    actual = model.evaluate
    observed = []

    def measures(candidate, rows):
        observed.append([row["event_id"] for row in rows])
        score = 0.02 if candidate["trained_rows"] > 64 else 0.01
        return actual(candidate, rows) | {"brier": score}

    monkeypatch.setattr(model, "evaluate", measures)
    report = learner.evaluate()["domains"]["execution"]
    assert report["reasons"] == ["incumbent_regression"]
    assert observed[0] == observed[1] and len(observed[0]) == 16
    assert learner.status()["snapshots"] == 1


def test_predictions_precede_learning_and_drift_reverts_to_static(learner):
    populate(learner)
    first = promote(learner)
    for index in range(16):
        assert observation(
            learner, choice="good" if index % 2 else "bad", success=not bool(index % 2)
        )
    recent = learner.recent(16)
    assert all(row["prediction"] is not None for row in recent)
    assert all((row["prediction"] > 0.5) != row["success"] for row in recent)
    state = learner.status()
    drift = state["domains"]["execution"]["drift"]
    assert drift["reverted_from"] == first["snapshot_id"] and drift["restored"] is None
    assert drift["heuristic"] == "recent_16_brier"
    assert drift["brier"] > drift["baseline_brier"] + 0.08
    assert state["promotion_paused"] and not state["paused"]
    assert not recommend(learner)["applied"]
    assert observation(learner)
    learner.control("resume")
    assert not learner.status()["promotion_paused"]


def test_pause_and_rollback_are_persistent_and_reversible(learner, tmp_path):
    populate(learner)
    first = promote(learner)
    populate(learner, 16, start=80)
    second = promote(learner)
    assert second["snapshot_id"] != first["snapshot_id"]
    state = learner.control("rollback")
    assert state["paused"] and state["promotion_paused"]
    assert state["domains"]["execution"]["active_id"] == first["snapshot_id"]
    assert observation(learner) is None
    assert learner.evaluate()["reason"] == "paused"
    assert recommend(learner)["reason"] == "paused"
    restored = LearningService(tmp_path)
    assert restored.status()["paused"]
    restored.control("resume")
    assert recommend(restored)["snapshot_id"] == first["snapshot_id"]
    assert observation(restored)
    restored.control("pause")
    assert observation(learner) is None
    restored.close()


def test_automatic_evaluation_needs_new_labels_and_time_but_explicit_evaluation_overrides(
    learner, monkeypatch
):
    monkeypatch.setattr(module, "EVALUATE_EVERY", 32)
    now = [2_000_000_000.0]
    monkeypatch.setattr(module.time, "time", lambda: now[0])
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    populate(learner, 95)
    assert learner.status()["snapshots"] == 0
    populate(learner, 1, start=95)
    assert learner.status()["snapshots"] == 1
    populate(learner, 64, start=96)
    assert learner.status()["domains"]["execution"]["last_evaluated_seq"] == 96
    assert learner.evaluate()["evaluated"]
    now[0] += 6
    populate(learner, 16, start=160)
    assert learner.status()["domains"]["execution"]["last_auto_count"] == 160
    populate(learner, 16, start=176)
    assert learner.status()["domains"]["execution"]["last_auto_count"] == 192


def test_event_retention_is_bounded_and_training_never_uses_partial_old_groups(learner):
    populate(learner, 2016, group_id="large_group")
    assert learner.status()["events"] == module.MAX_EVENTS
    group = sql(learner, "SELECT * FROM groups")[0]
    assert group["first_seq"] == 1 and group["last_seq"] == 2016
    populate(learner, 80, start=3000)
    report = promote(learner)
    assert report["train"] == 64 and report["holdout"] == 16
    assert report["train_through_seq"] == 2080
    assert len(sql(learner, "SELECT * FROM groups")) <= module.MAX_EVENTS


def test_training_window_and_snapshot_history_are_bounded(learner, monkeypatch):
    populate(learner, 600)
    first = promote(learner)
    assert first["train"] == 512
    actual = model.evaluate

    def neutral_scores(candidate, rows):
        return actual(candidate, rows) | {"brier": 0.01}

    monkeypatch.setattr(model, "evaluate", neutral_scores)
    for cycle in range(8):
        populate(learner, 16, start=600 + cycle * 16)
        promote(learner)
    status = learner.status()
    assert status["snapshots"] == module.MAX_SNAPSHOTS
    before = status["domains"]["execution"]
    learner.control("rollback")
    assert learner.status()["domains"]["execution"]["active_id"] == before["previous_id"]


def test_six_snapshot_bound_preserves_each_domains_current_and_previous(learner, monkeypatch):
    actual = model.evaluate

    def neutral_scores(candidate, rows):
        return actual(candidate, rows) | {"brier": 0.01}

    monkeypatch.setattr(model, "evaluate", neutral_scores)
    for domain in sorted(module.DOMAINS):
        populate(learner, domain=domain)
        promote(learner, domain)
        for cycle in range(3):
            populate(learner, 16, start=80 + cycle * 16, domain=domain)
            promote(learner, domain)
    status = learner.status()
    assert status["snapshots"] == 6
    protected = {
        value[key] for value in status["domains"].values() for key in ("active_id", "previous_id")
    }
    assert len(protected) == 6
    assert {row["id"] for row in sql(learner, "SELECT id FROM snapshots")} == protected


def test_retention_uses_bounded_sqlite_steps_and_gate_detects_missing_group_index(learner):
    populate(learner, module.MAX_EVENTS)
    conn = learner._connection
    # At the 2,000-row cap, one indexed eviction measured 4,279 VM steps;
    # the prior all-groups sweep cost 52,275. This permits SQLite variation
    # while rejecting either the old sweep or a missing group lookup index.
    step_limit = 4 * module.MAX_EVENTS

    def measure_observation():
        steps = [0]

        def progress():
            steps[0] += 100
            # Abort exactly once, allowing the service's fail-open rollback to finish.
            return int(steps[0] == step_limit)

        conn.set_progress_handler(progress, 100)
        try:
            event = observation(learner)
        finally:
            conn.set_progress_handler(None, 0)
        return event, steps[0]

    event, steps = measure_observation()
    assert event and steps < step_limit
    conn.execute("DROP INDEX grouped_events")
    try:
        event, steps = measure_observation()
        assert event is None and steps >= step_limit
    finally:
        conn.execute("CREATE INDEX grouped_events ON events(domain,group_id)")
    assert measure_observation()[0]


def test_corrupt_model_abstains_until_validated_recovery(learner):
    populate(learner)
    promote(learner)
    saved = sql(learner, "SELECT model_json FROM snapshots")[0]["model_json"]
    sql(learner, "UPDATE snapshots SET model_json=?", ('{"secret": "do not echo"}',))
    result = recommend(learner)
    assert not result["applied"] and "secret" not in json.dumps(result)
    assert recommend(learner)["reason"] == "unhealthy"
    with pytest.raises(TeeError) as error:
        learner.status()
    assert "secret" not in str(error.value)
    sql(learner, "UPDATE snapshots SET model_json=?", (saved,))
    assert recommend(learner)["reason"] == "unhealthy"
    assert learner.status()["health"] == "ok"
    assert recommend(learner)["applied"]


def test_storage_failure_is_fail_open_but_explicit_methods_fail_cheaply(tmp_path):
    service = LearningService(tmp_path)
    service.path.parent.mkdir(parents=True)
    service.path.write_bytes(b"corrupt database with secret payload")
    assert observation(service) is None
    with pytest.raises(TeeError) as error:
        service.recent()
    assert len(str(error.value)) < 100 and "secret" not in str(error.value)
    assert not recommend(service)["applied"]


@pytest.mark.parametrize(
    "candidates", [[], CANDIDATES * 2, [{"choice": "x", "version": "v", "text": "secret"}]]
)
def test_invalid_explicit_recommendations_are_short_errors_without_writes(tmp_path, candidates):
    service = LearningService(tmp_path)
    with pytest.raises(TeeError) as error:
        service.recommend("execution", "fixture", candidates)
    assert "secret" not in str(error.value)
    assert not service.path.exists()


@pytest.mark.parametrize("limit", [0, 51, True, "10"])
def test_recent_refuses_unbounded_or_noninteger_queries(learner, limit):
    with pytest.raises(TeeError):
        learner.recent(limit)
