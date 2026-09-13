"""Bounded, deterministic contextual learning with no optional dependencies.

Only domain/context/choice/version enter features. The service owns provenance,
chronological group splits, promotion and retention. These numerical models
predict observed reliability and cost; they do not estimate unobserved policy
speedups. No prompts, payloads, row IDs or group IDs enter the learned features.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_VERSION = 1
FEATURE_COUNT = 256
MAX_ROWS = 4096
MAX_IDENTIFIER_LENGTH = 256
MAX_COST = 1e12
MAX_LOG_COST = math.log1p(MAX_COST)
EPOCHS = 16
WEIGHT_BOUND = 16.0
IDENTIFIERS = ("domain", "context", "choice", "version")


def _identifiers(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    if not isinstance(row, Mapping):
        raise ValueError("learning row must be a mapping")
    values = []
    for name in IDENTIFIERS:
        value = row.get(name)
        if not isinstance(value, str) or not value.strip() or len(value) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(f"{name} must be a nonempty identifier of at most 256 characters")
        values.append(value)
    return values[0], values[1], values[2], values[3]


def _cost(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a finite nonnegative number")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite nonnegative number") from exc
    if not math.isfinite(number) or not 0 <= number <= MAX_COST:
        raise ValueError(f"{name} must be finite and between 0 and {MAX_COST:g}")
    return number


def _rows(rows: Sequence[Mapping[str, Any]], *, allow_empty: bool = False) -> list[dict[str, Any]]:
    if not isinstance(rows, list | tuple) or len(rows) > MAX_ROWS:
        raise ValueError(f"learning requires at most {MAX_ROWS} rows")
    if not rows and not allow_empty:
        raise ValueError("learning requires at least one labelled row")
    clean = []
    for row in rows:
        identifiers = _identifiers(row)
        if type(row.get("success")) is not bool:
            raise ValueError("success must be a verified or explicitly labelled boolean")
        item = dict(zip(IDENTIFIERS, identifiers, strict=True))
        item["success"] = row["success"]
        item["elapsed_ms"] = _cost(row.get("elapsed_ms"), "elapsed_ms")
        item["tokens"] = None if row.get("tokens") is None else _cost(row["tokens"], "tokens")
        clean.append(item)
    if len({row["domain"] for row in clean}) > 1:
        raise ValueError("learning domains must be fitted and evaluated separately")
    return clean


def _support_key(row: Mapping[str, Any]) -> str:
    identifiers = _identifiers(row)
    encoded = json.dumps(identifiers, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _features(row: Mapping[str, Any]) -> dict[int, float]:
    _, context, choice, version = _identifiers(row)
    # Pair/triple terms learn that the same strategy can work in one context
    # and fail in another. ID/group_id/success/cost never enter this dictionary.
    terms = (
        ("context", context),
        ("choice", choice),
        ("version", version),
        ("context-choice", context, choice),
        ("choice-version", choice, version),
        ("context-version", context, version),
        ("all", context, choice, version),
    )
    sparse: dict[int, float] = {}
    for term in terms:
        digest = hashlib.sha256(json.dumps(term, separators=(",", ":")).encode()).digest()
        index = 1 + int.from_bytes(digest[:4], "big") % (FEATURE_COUNT - 1)
        sparse[index] = sparse.get(index, 0.0) + (1.0 if digest[4] & 1 else -1.0)
    norm = math.sqrt(sum(value * value for value in sparse.values())) or 1.0
    return {0: 1.0, **{index: value / norm for index, value in sparse.items() if value}}


def _dot(weights: list[float], features: dict[int, float]) -> float:
    return sum(weights[index] * value for index, value in features.items())


def _sigmoid(value: float) -> float:
    value = max(-30.0, min(30.0, value))
    return 1 / (1 + math.exp(-value))


def _step(weights: list[float], features: dict[int, float], gradient: float, rate: float) -> None:
    for index, value in features.items():
        weights[index] = max(
            -WEIGHT_BOUND, min(WEIGHT_BOUND, weights[index] - rate * gradient * value)
        )


def _constant(rows: list[dict[str, Any]]) -> dict[str, float | int | None]:
    token_logs = [math.log1p(row["tokens"]) for row in rows if row["tokens"] is not None]
    return {
        "success_base": sum(row["success"] for row in rows) / len(rows),
        "cost_log_base": math.fsum(math.log1p(row["elapsed_ms"]) for row in rows) / len(rows),
        "token_log_base": math.fsum(token_logs) / len(token_logs) if token_logs else None,
        "token_rows": len(token_logs),
    }


def fit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit only the supplied training rows, in deterministic supplied order.

    Uses projected SGD for logistic loss and squared log1p cost error. The
    service invokes bounded refits as observations arrive; this function never
    reads a store, learns from a holdout, starts a timer or performs I/O.
    """
    clean = _rows(rows)
    constants = _constant(clean)
    success = [0.0] * FEATURE_COUNT
    cost = [0.0] * FEATURE_COUNT
    tokens = [0.0] * FEATURE_COUNT if constants["token_rows"] else None
    smoothed = (sum(row["success"] for row in clean) + 1) / (len(clean) + 2)
    success[0] = math.log(smoothed / (1 - smoothed))
    cost[0] = float(constants["cost_log_base"])
    if tokens is not None:
        tokens[0] = float(constants["token_log_base"])
    support: dict[str, int] = {}
    features = []
    for row in clean:
        key = _support_key(row)
        support[key] = support.get(key, 0) + 1
        features.append(_features(row))
    for epoch in range(EPOCHS):
        probability_rate = 0.4 / (1 + 0.15 * epoch)
        cost_rate = 0.12 / (1 + 0.1 * epoch)
        for row, feature in zip(clean, features, strict=True):
            error = _sigmoid(_dot(success, feature)) - int(row["success"])
            _step(success, feature, error, probability_rate)
            error = _dot(cost, feature) - math.log1p(row["elapsed_ms"])
            _step(cost, feature, max(-5.0, min(5.0, error)), cost_rate)
            if tokens is not None and row["tokens"] is not None:
                error = _dot(tokens, feature) - math.log1p(row["tokens"])
                _step(tokens, feature, max(-5.0, min(5.0, error)), cost_rate)
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": "hashed-logistic-sgd-v1",
        "domain": clean[0]["domain"],
        "feature_count": FEATURE_COUNT,
        "trained_rows": len(clean),
        **constants,
        "weights": {"success": success, "cost": cost, "tokens": tokens},
        "support": support,
    }


def _model(model: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(model, Mapping):
        raise ValueError("learning model must be a mapping")
    if (
        model.get("schema_version") != SCHEMA_VERSION
        or model.get("feature_count") != FEATURE_COUNT
        or model.get("algorithm") != "hashed-logistic-sgd-v1"
    ):
        raise ValueError("unsupported learning model schema")
    domain = model.get("domain")
    if not isinstance(domain, str) or not domain or len(domain) > MAX_IDENTIFIER_LENGTH:
        raise ValueError("learning model has an invalid domain")
    weights = model.get("weights")
    if not isinstance(weights, Mapping):
        raise ValueError("learning model has no weight vectors")
    for name in ("success", "cost", "tokens"):
        vector = weights.get(name)
        if vector is None and name == "tokens":
            continue
        if (
            not isinstance(vector, list)
            or len(vector) != FEATURE_COUNT
            or any(
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or abs(value) > WEIGHT_BOUND
                or not math.isfinite(value)
                for value in vector
            )
        ):
            raise ValueError(f"learning model has an invalid {name} weight vector")
    support = model.get("support")
    if (
        not isinstance(support, Mapping)
        or len(support) > MAX_ROWS
        or any(
            not isinstance(key, str)
            or len(key) != 64
            or type(value) is not int
            or not 1 <= value <= MAX_ROWS
            for key, value in support.items()
        )
    ):
        raise ValueError("learning model has invalid support counts")
    trained_rows = model.get("trained_rows")
    token_rows = model.get("token_rows")
    if (
        type(trained_rows) is not int
        or not 1 <= trained_rows <= MAX_ROWS
        or sum(support.values()) != trained_rows
        or type(token_rows) is not int
        or not 0 <= token_rows <= trained_rows
        or (weights.get("tokens") is None) != (token_rows == 0)
    ):
        raise ValueError("learning model has inconsistent observation counts")
    for name, upper in (
        ("success_base", 1.0),
        ("cost_log_base", MAX_LOG_COST),
        ("token_log_base", MAX_LOG_COST),
    ):
        value = model.get(name)
        if name == "token_log_base" and token_rows == 0 and value is None:
            continue
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not 0 <= value <= upper
            or not math.isfinite(value)
        ):
            raise ValueError(f"learning model has an invalid {name}")
    return dict(model)


def _predict(model: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, float]:
    domain, _, _, _ = _identifiers(row)
    if domain != model["domain"]:
        raise ValueError("learning model domain does not match the row")
    feature = _features(row)
    weights = model["weights"]
    prediction = {
        "success_probability": _sigmoid(_dot(weights["success"], feature)),
        "elapsed_ms": math.expm1(max(0.0, min(MAX_LOG_COST, _dot(weights["cost"], feature)))),
    }
    if weights["tokens"] is not None:
        prediction["tokens"] = math.expm1(
            max(0.0, min(MAX_LOG_COST, _dot(weights["tokens"], feature)))
        )
    return prediction


def predict(model: dict[str, Any], row: dict[str, Any]) -> dict[str, float]:
    """Predict from four identifiers; observed labels and arbitrary payloads are ignored."""
    return _predict(_model(model), row)


def covered(model: dict[str, Any] | None, row: dict[str, Any], min_samples: int = 6) -> bool:
    """Exact context/choice/version support, independent of a probability prediction."""
    if type(min_samples) is not int or min_samples < 1:
        raise ValueError("min_samples must be a positive integer")
    if model is None:
        return False
    checked = _model(model)
    domain, _, _, _ = _identifiers(row)
    return (
        domain == checked["domain"] and checked["support"].get(_support_key(row), 0) >= min_samples
    )


def _metrics(rows: list[dict[str, Any]], predictions: list[dict[str, float]]) -> dict[str, Any]:
    brier, cost_errors, token_errors = [], [], []
    for row, prediction in zip(rows, predictions, strict=True):
        brier.append((prediction["success_probability"] - int(row["success"])) ** 2)
        cost_errors.append(
            abs(math.log1p(prediction["elapsed_ms"]) - math.log1p(row["elapsed_ms"]))
        )
        if row["tokens"] is not None and "tokens" in prediction:
            token_errors.append(abs(math.log1p(prediction["tokens"]) - math.log1p(row["tokens"])))
    return {
        "count": len(rows),
        "brier": math.fsum(brier) / len(brier) if brier else None,
        "cost_log_mae": math.fsum(cost_errors) / len(cost_errors) if cost_errors else None,
        "token_count": len(token_errors),
        "token_log_mae": math.fsum(token_errors) / len(token_errors) if token_errors else None,
    }


def evaluate(model: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate without training or mutating the model. Costs are natural-log1p MAE."""
    checked = _model(model)
    clean = _rows(rows, allow_empty=True)
    return _metrics(clean, [_predict(checked, row) for row in clean])


def baseline(train: list[dict[str, Any]], heldout: list[dict[str, Any]]) -> dict[str, Any]:
    """Score train-only constants on heldout rows; no heldout value informs a prediction."""
    clean = _rows(train)
    test = _rows(heldout, allow_empty=True)
    if test and clean[0]["domain"] != test[0]["domain"]:
        raise ValueError("baseline training and heldout domains must match")
    constants = _constant(clean)
    prediction = {
        "success_probability": float(constants["success_base"]),
        "elapsed_ms": math.expm1(float(constants["cost_log_base"])),
    }
    if constants["token_log_base"] is not None:
        prediction["tokens"] = math.expm1(float(constants["token_log_base"]))
    return _metrics(test, [prediction] * len(test))
