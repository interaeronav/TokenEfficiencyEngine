"""A45 P2b — portfolio optimisation, compactly.

PyPortfolioOpt (MIT) for the classic mean-variance objectives and
hierarchical risk parity; skfolio (BSD-3) for its scikit-learn-shaped
estimators. Both are pure in-process libraries: no service, no network at
fit time, no display.

Token discipline is the reason this module exists rather than a thin
passthrough. The natural output of a portfolio optimiser is a weight
vector plus an NxN covariance matrix - for 500 assets that is 250,000
numbers nobody asked for. So an answer is: the weights that are actually
non-trivial, rounded, plus expected return / volatility / Sharpe, plus a
`weights_id`. The full vector and the risk model are a second, explicit
`quant_detail` call.

Nothing here gives advice. It reports what an optimiser computed from the
numbers it was handed; whether those numbers describe the future is not a
question arithmetic can answer, and the payload says so.
"""

from __future__ import annotations

import time
from typing import Any

from tee.fleet.probe import need, probe_rows
from tee.fleet.quiet import muted_stdout
from tee.kernel.errors import TeeError

METHODS = ("max_sharpe", "min_volatility", "hrp", "mean_risk")
DEFAULT_SHOW = 15
SHOW_CAP = 200
MIN_WEIGHT = 1e-4

_STORE: dict[str, dict[str, Any]] = {}
_STORE_CAP = 16
_SEQ = [0]

NOT_ADVICE = (
    "Arithmetic over the series supplied, not investment advice: the "
    "optimiser assumes the past sample describes the future, which is the "
    "assumption that fails in practice."
)


def _remember(payload: dict[str, Any]) -> str:
    _SEQ[0] += 1
    wid = f"w_{_SEQ[0]}"
    _STORE[wid] = payload
    while len(_STORE) > _STORE_CAP:
        _STORE.pop(next(iter(_STORE)))
    return wid


def _frame(spec: dict[str, Any]):
    """Accept {'prices': {...}} or {'returns': {...}} -> (returns, prices)."""
    pd = need("pandas", "quant", what="the dataframe layer")
    prices_in = spec.get("prices")
    returns_in = spec.get("returns")
    if not prices_in and not returns_in:
        raise TeeError(
            "quant_bad_spec",
            "Supply either `prices` or `returns`.",
            fix='prices: {"AAA": [100, 101, ...], "BBB": [...]} - equal lengths, oldest first.',
        )
    raw = prices_in or returns_in
    if not isinstance(raw, dict) or not raw:
        raise TeeError(
            "quant_bad_spec",
            "prices/returns must be an object of {asset: [numbers]}.",
            fix='e.g. {"AAA": [100, 101, 99], "BBB": [50, 51, 52]}',
        )
    lengths = {k: len(v or []) for k, v in raw.items()}
    if len(set(lengths.values())) != 1:
        raise TeeError(
            "quant_bad_spec",
            f"series have different lengths: {lengths}",
            fix="Align the series to one common date range first.",
        )
    n = next(iter(lengths.values()))
    if n < 20:
        raise TeeError(
            "quant_bad_spec",
            f"{n} observations is too few to estimate a covariance.",
            fix="Supply at least 20, and prefer a few hundred.",
        )
    df = pd.DataFrame({k: [float(x) for x in v] for k, v in raw.items()})
    if prices_in:
        return df.pct_change().dropna(), df
    return df, (1.0 + df).cumprod()


def optimize(spec: dict[str, Any]) -> dict[str, Any]:
    method = str(spec.get("method") or "max_sharpe").lower()
    if method not in METHODS:
        raise TeeError(
            "quant_bad_method",
            f"'{method}' is not a method.",
            fix=f"Use one of: {', '.join(METHODS)}.",
        )
    show = max(1, min(int(spec.get("show") or DEFAULT_SHOW), SHOW_CAP))
    returns, prices = _frame(spec)
    started = time.monotonic()

    if method == "mean_risk":
        weights, extra = _skfolio(returns, spec)
    else:
        weights, extra = _pypfopt(returns, prices, method, spec)
    wall = round(time.monotonic() - started, 4)
    extra.update(_perf(returns, weights, spec))

    total = float(sum(weights.values())) or 1.0
    held = {k: round(v, 6) for k, v in weights.items() if abs(v) >= MIN_WEIGHT}
    ranked = sorted(held.items(), key=lambda kv: -abs(kv[1]))
    wid = _remember(
        {
            "weights": {k: round(float(v), 9) for k, v in weights.items()},
            "method": method,
            "assets": list(returns.columns),
            "n_obs": len(returns),
            **extra,
        }
    )

    out: dict[str, Any] = {
        "ok": True,
        "method": method,
        "engine": extra.get("engine"),
        "n_assets": len(weights),
        "n_held": len(held),
        "n_observations": len(returns),
        "weights_sum": round(total, 6),
        "weights": dict(ranked[:show]),
        "weights_id": wid,
        "wall_s": wall,
        "note": NOT_ADVICE,
    }
    for k in ("expected_return", "volatility", "sharpe"):
        if extra.get(k) is not None:
            out[k] = round(float(extra[k]), 6)
    out["basis"] = (
        f"annualised over {int(extra['periods_per_year'])} periods, "
        f"risk_free_rate={extra['risk_free_rate']} - computed by TEE for ALL "
        f"methods so they are comparable (the libraries' own numbers are not)"
    )
    if len(ranked) > show:
        out["truncated"] = (
            f"{len(ranked) - show} more holdings - quant_detail "
            f"{{weights_id: '{wid}'}} returns all of them"
        )
    return out


def _perf(returns, weights: dict[str, float], spec: dict[str, Any]) -> dict[str, Any]:
    """Performance computed HERE, identically for every method.

    Each library reports its own way and the numbers are not comparable:
    measured on this machine, `HRPOpt.portfolio_performance` defaults to
    risk_free_rate=0 and an arithmetic mean, while `EfficientFrontier`
    reports against the GEOMETRIC mu it optimised on with rf=0.02. Same
    portfolio, two answers - and HRP looked twice as good as max_sharpe,
    which would be a wrong conclusion drawn from a units mismatch. So the
    engines optimise; this function measures, on one estimator and one
    risk-free rate, so `method` comparisons mean something.
    """
    periods = float(spec.get("periods_per_year") or 252)
    rf = float(spec.get("risk_free_rate") or 0.02)
    cols = list(returns.columns)
    w = [float(weights.get(c, 0.0)) for c in cols]
    port = (returns[cols] * w).sum(axis=1)
    mean = float(port.mean()) * periods
    vol = float(port.std(ddof=1)) * (periods**0.5)
    return {
        "expected_return": mean,
        "volatility": vol,
        "sharpe": ((mean - rf) / vol) if vol else None,
        "periods_per_year": periods,
        "risk_free_rate": rf,
    }


def _pypfopt(returns, prices, method: str, spec: dict[str, Any]):
    need("pypfopt", "quant", what="PyPortfolioOpt")
    from pypfopt import EfficientFrontier, expected_returns, risk_models
    from pypfopt.hierarchical_portfolio import HRPOpt

    with muted_stdout():
        if method == "hrp":
            h = HRPOpt(returns)
            h.optimize()
            w = h.clean_weights()
        else:
            mu = expected_returns.mean_historical_return(prices)
            S = risk_models.sample_cov(prices)
            ef = EfficientFrontier(mu, S, weight_bounds=_bounds(spec))
            rf = float(spec.get("risk_free_rate") or 0.02)
            if method == "max_sharpe":
                try:
                    ef.max_sharpe(risk_free_rate=rf)
                except ValueError as exc:
                    # A real and common case, not an edge: in a flat or
                    # falling sample no asset clears the hurdle, and the
                    # library raises a bare ValueError. Rule 6 - one short
                    # message with the exact fix.
                    best = float(max(mu)) if len(mu) else 0.0
                    raise TeeError(
                        "quant_no_asset_beats_rf",
                        f"No asset's expected return ({best:.2%} at best) exceeds "
                        f"the risk-free rate ({rf:.2%}), so a maximum-Sharpe "
                        f"portfolio is undefined.",
                        fix=f"Lower risk_free_rate below {best:.4f}, or use "
                        f"method='min_volatility' / 'hrp', which do not need "
                        f"a positive excess return.",
                    ) from exc
            else:
                ef.min_volatility()
            w = ef.clean_weights()
    return {str(k): float(v) for k, v in w.items()}, {"engine": "pyportfolioopt"}


def _bounds(spec: dict[str, Any]):
    lo = spec.get("min_weight")
    hi = spec.get("max_weight")
    if lo is None and hi is None:
        return (0, 1)
    return (float(lo if lo is not None else 0), float(hi if hi is not None else 1))


def _skfolio(returns, spec: dict[str, Any]):
    need("skfolio", "quant", what="skfolio")
    from skfolio import RiskMeasure
    from skfolio.optimization import MeanRisk

    measure = str(spec.get("risk_measure") or "variance").upper()
    try:
        rm = getattr(RiskMeasure, measure)
    except AttributeError as exc:
        avail = [m for m in dir(RiskMeasure) if m.isupper()][:12]
        raise TeeError(
            "quant_bad_spec",
            f"risk_measure '{measure}' is unknown.",
            fix=f"Try one of: {', '.join(avail)}.",
        ) from exc
    with muted_stdout():
        model = MeanRisk(risk_measure=rm)
        model.fit(returns)
        w = dict(zip(list(returns.columns), [float(x) for x in model.weights_], strict=False))
    return w, {"engine": "skfolio"}


def detail(weights_id: str, offset: int = 0, limit: int = 100) -> dict[str, Any]:
    payload = _STORE.get(str(weights_id))
    if payload is None:
        raise TeeError(
            "quant_unknown_weights",
            f"No weights '{weights_id}' in this session.",
            fix=f"Known: {', '.join(_STORE) or '(none yet)'}. Re-run quant_optimize.",
        )
    items = sorted(payload["weights"].items(), key=lambda kv: -abs(kv[1]))
    offset = max(0, int(offset))
    limit = max(1, min(int(limit), 1000))
    page = items[offset : offset + limit]
    return {
        "weights_id": weights_id,
        "method": payload["method"],
        "n_observations": payload["n_obs"],
        "offset": offset,
        "returned": len(page),
        "total": len(items),
        "weights": dict(page),
        "note": NOT_ADVICE,
    }


def backends() -> dict[str, Any]:
    rows = probe_rows({"pyportfolioopt": "pypfopt", "skfolio": "skfolio", "pandas": "pandas"})
    ready = [k for k, v in rows.items() if v.get("installed")]
    return {
        "backends": rows,
        "ready": ready,
        "methods": list(METHODS),
        "fix": None if len(ready) >= 2 else "uv pip install 'tee-engine[quant]'",
    }
