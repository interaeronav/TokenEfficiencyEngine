"""Actual learned coefficients and held-out prediction quality, not policy speed claims."""

from __future__ import annotations

import copy
import json
import math

import pytest

from tee.learning import model


def _row(index: int = 0, **changes):
    return {
        "id": index,
        "group_id": f"task-{index}",
        "domain": "verified",
        "context": "sketch",
        "choice": "small",
        "version": "engine-v1",
        "success": True,
        "elapsed_ms": 10.0,
        "tokens": 20,
        **changes,
    }


def _pattern(start: int, count: int):
    rows = []
    for index in range(start, start + count):
        context = "sketch" if index % 4 < 2 else "render"
        choice = "small" if index % 2 == 0 else "large"
        succeeds = (context == "sketch") == (choice == "small")
        rows.append(
            _row(
                index,
                context=context,
                choice=choice,
                success=succeeds,
                elapsed_ms=12.0 if succeeds else 600.0,
                tokens=40 if succeeds else 800,
            )
        )
    return rows


def test_learns_context_choice_interaction_on_later_unseen_task_groups():
    train, heldout = _pattern(0, 128), _pattern(128, 64)
    assert not {row["group_id"] for row in train} & {row["group_id"] for row in heldout}
    learned = model.fit(train)
    score = model.evaluate(learned, heldout)
    constant = model.baseline(train, heldout)
    assert score["brier"] < constant["brier"] / 4
    assert score["cost_log_mae"] < constant["cost_log_mae"] / 4
    assert score["token_log_mae"] < constant["token_log_mae"] / 4
    assert score["count"] == score["token_count"] == 64
    small_sketch = model.predict(learned, _row(context="sketch", choice="small"))
    small_render = model.predict(learned, _row(context="render", choice="small"))
    assert small_sketch["success_probability"] > 0.8
    assert small_render["success_probability"] < 0.2
    assert small_sketch["elapsed_ms"] < small_render["elapsed_ms"]


def test_training_is_deterministic_json_roundtrippable_and_evaluation_does_not_learn():
    rows = _pattern(0, 40)
    before = copy.deepcopy(rows)
    first = model.fit(rows)
    assert first == model.fit(rows)
    assert rows == before
    restored = json.loads(json.dumps(first, allow_nan=False))
    frozen = copy.deepcopy(restored)
    model.evaluate(restored, _pattern(40, 16))
    model.predict(restored, _row())
    assert restored == frozen
    assert model.predict(restored, _row()) == model.predict(first, _row())


def test_only_pre_action_identifiers_enter_features_and_model_state():
    train = _pattern(0, 32)
    decorated = [
        dict(
            row,
            prompt="SECRET prompt text",
            code="arbitrary code",
            payload={"path": "/private/secret"},
            output="SECRET output",
            id=9_000 + index,
            group_id=f"other-{index}",
        )
        for index, row in enumerate(train)
    ]
    assert model.fit(train) == model.fit(decorated)
    learned = model.fit(decorated)
    assert "SECRET" not in json.dumps(learned)
    first = model.predict(learned, _row())
    assert first == model.predict(
        learned,
        _row(
            success=False,
            elapsed_ms=999,
            tokens=999,
            prompt="different",
            group_id="unknown",
            id=-99,
        ),
    )


def test_support_requires_exact_context_choice_version_and_domain():
    learned = model.fit([_row(index) for index in range(6)])
    assert model.covered(learned, _row())
    assert not model.covered(learned, _row(), min_samples=7)
    for changes in (
        {"context": "new"},
        {"choice": "new"},
        {"version": "engine-v2"},
        {"domain": "execution"},
    ):
        assert not model.covered(learned, _row(**changes))
    assert not model.covered(None, _row())
    with pytest.raises(ValueError, match="min_samples"):
        model.covered(learned, _row(), min_samples=0)


def test_versions_do_not_share_support_even_when_context_and_choice_match():
    learned = model.fit([_row(index, version="v1" if index < 3 else "v2") for index in range(6)])
    assert not model.covered(learned, _row(version="v1"))
    assert not model.covered(learned, _row(version="v2"))
    assert model.covered(learned, _row(version="v2"), min_samples=3)


def test_missing_token_observations_stay_unknown_not_zero():
    learned = model.fit([_row(index, tokens=None) for index in range(8)])
    assert "tokens" not in model.predict(learned, _row())
    assert learned["token_rows"] == 0
    assert learned["token_log_base"] is None
    score = model.evaluate(learned, [_row()])
    assert score["token_count"] == 0 and score["token_log_mae"] is None
    assert model.baseline([_row(tokens=None)], [_row()])["token_log_mae"] is None


def test_partly_observed_tokens_score_only_observed_rows():
    learned = model.fit([_row(index, tokens=10 if index % 2 else None) for index in range(8)])
    score = model.evaluate(learned, [_row(tokens=None), _row(tokens=10)])
    assert score["count"] == 2 and score["token_count"] == 1
    assert learned["token_rows"] == 4
    assert model.predict(learned, _row())["tokens"] > 0


def test_baseline_uses_training_means_in_log_cost_space_only():
    train = [
        _row(success=False, elapsed_ms=0, tokens=None),
        _row(success=True, elapsed_ms=8, tokens=None),
    ]
    score = model.baseline(train, [_row(success=True, elapsed_ms=80, tokens=999)])
    assert score["brier"] == pytest.approx(0.25)
    assert score["cost_log_mae"] == pytest.approx(math.log1p(80) - math.log1p(8) / 2)
    assert score["token_count"] == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"elapsed_ms": float("nan")},
        {"elapsed_ms": float("inf")},
        {"elapsed_ms": -1},
        {"elapsed_ms": "4"},
        {"elapsed_ms": True},
        {"elapsed_ms": 1e13},
        {"tokens": float("nan")},
        {"tokens": -1},
        {"tokens": True},
        {"success": 1},
        {"success": None},
        {"domain": ""},
        {"context": " "},
        {"choice": "x" * 257},
        {"version": None},
    ],
)
def test_invalid_or_nonfinite_training_values_fail_loudly(changes):
    with pytest.raises(ValueError):
        model.fit([_row(**changes)])


def test_finite_predictions_and_bounded_state_with_extreme_valid_labels():
    learned = model.fit(
        [
            _row(
                index,
                success=bool(index % 2),
                elapsed_ms=model.MAX_COST if index % 2 else 0,
                tokens=model.MAX_COST if index % 2 else 0,
            )
            for index in range(24)
        ]
    )
    prediction = model.predict(learned, _row())
    assert all(math.isfinite(value) for value in prediction.values())
    assert 0 < prediction["success_probability"] < 1
    assert 0 <= prediction["elapsed_ms"] <= model.MAX_COST * (1 + 1e-12)
    assert 0 <= prediction["tokens"] <= model.MAX_COST * (1 + 1e-12)
    for weights in learned["weights"].values():
        assert len(weights) == model.FEATURE_COUNT
        assert max(abs(weight) for weight in weights) <= model.WEIGHT_BOUND


def test_empty_holdout_is_unknown_and_empty_training_is_rejected():
    learned = model.fit([_row()])
    assert model.evaluate(learned, []) == {
        "count": 0,
        "brier": None,
        "cost_log_mae": None,
        "token_count": 0,
        "token_log_mae": None,
    }
    assert model.baseline([_row()], [])["count"] == 0
    with pytest.raises(ValueError, match="at least one"):
        model.fit([])


def test_row_limit_prevents_unbounded_training():
    with pytest.raises(ValueError, match="at most"):
        model.fit([_row()] * (model.MAX_ROWS + 1))


def test_learning_domains_are_never_pooled():
    with pytest.raises(ValueError, match="separately"):
        model.fit([_row(), _row(domain="execution")])
    learned = model.fit([_row()])
    with pytest.raises(ValueError, match="domain"):
        model.predict(learned, _row(domain="execution"))
    with pytest.raises(ValueError, match="domain"):
        model.baseline([_row()], [_row(domain="execution")])


@pytest.mark.parametrize("mutation", ["schema", "nan", "missing", "support"])
def test_corrupt_model_snapshots_fail_with_value_error(mutation):
    learned = model.fit([_row()])
    if mutation == "schema":
        learned["schema_version"] = 99
    elif mutation == "nan":
        learned["weights"]["cost"][0] = float("nan")
    elif mutation == "missing":
        del learned["weights"]["success"]
    else:
        learned["support"] = {"bad": -1}
    with pytest.raises(ValueError):
        model.predict(learned, _row())


def test_probability_gradient_matches_central_difference():
    z, y, epsilon = 0.7, 1.0, 1e-6

    def loss(value):
        probability = model._sigmoid(value)
        return -y * math.log(probability) - (1 - y) * math.log1p(-probability)

    numerical = (loss(z + epsilon) - loss(z - epsilon)) / (2 * epsilon)
    assert numerical == pytest.approx(model._sigmoid(z) - y, rel=1e-6)


def test_noisy_probabilities_are_calibrated_on_a_controlled_heldout_fixture():
    rows = []
    for index in range(240):
        context = "a" if index % 2 == 0 else "b"
        label = (index // 2) % 5 < (4 if context == "a" else 1)
        rows.append(_row(index, context=context, success=label))
    learned = model.fit(rows[:200])
    for context, expected in (("a", 0.8), ("b", 0.2)):
        probability = model.predict(learned, _row(context=context))["success_probability"]
        assert abs(probability - expected) < 0.06
    assert model.evaluate(learned, rows[200:])["brier"] < 0.18
    assert model.baseline(rows[:200], rows[200:])["brier"] == pytest.approx(0.25)


def test_overflowing_integers_are_rejected_as_values_not_uncaught_overflows():
    with pytest.raises(ValueError, match="finite"):
        model.fit([_row(elapsed_ms=10**1000)])
    learned = model.fit([_row()])
    learned["weights"]["success"][0] = 10**1000
    with pytest.raises(ValueError, match="weight"):
        model.predict(learned, _row())


@pytest.mark.parametrize(
    "key,value",
    [
        ("trained_rows", 99),
        ("token_rows", -1),
        ("success_base", float("nan")),
        ("cost_log_base", float("inf")),
    ],
)
def test_inconsistent_snapshot_metadata_is_rejected(key, value):
    learned = model.fit([_row()])
    learned[key] = value
    with pytest.raises(ValueError):
        model.predict(learned, _row())


def test_model_module_uses_only_stdlib_and_has_no_io_surface():
    import ast
    import inspect
    import sys

    tree = ast.parse(inspect.getsource(model))
    imported = []
    banned_calls = {"open", "eval", "exec", "__import__"}
    banned_attributes = {
        "read_text",
        "write_text",
        "read_bytes",
        "write_bytes",
        "connect",
        "urlopen",
        "request",
        "socket",
        "Popen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            assert not (isinstance(node.func, ast.Name) and node.func.id in banned_calls)
            assert not (
                isinstance(node.func, ast.Attribute) and node.func.attr in banned_attributes
            )
    assert set(imported) <= sys.stdlib_module_names
