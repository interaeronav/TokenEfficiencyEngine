"""A45 P2f — trading RESEARCH. Backtests and nothing else.

**What this module cannot do, structurally.** It places no order, amends
none, cancels none, moves no funds, starts and stops no strategy, and
toggles no simulated/live switch. Not in live mode, not in paper mode, not
behind a confirmation, not with a config flag. There is no code path here
that reaches a broker, and no tool name in the trust table that could
acquire one: `place-order` is reserved and ungrantable, and `trade_*` has
no family prefix, so an untabled trade tool is a startup error rather than
an open-tier default.

It also **never touches a credential**. That is not squeamishness: on
OpenAlgo the same API key that reads an account also reaches
`POST /api/v1/analyzer/toggle`, which flips simulated mode to live; on
hummingbot-api one HTTP Basic credential serves every endpoint. The
credential is the hazard, not the verb, so there are no live account reads
either.

**Signals are DECLARATIVE, not code.** A rule is `{"kind": "sma_cross",
"fast": 20, "slow": 50}`, evaluated by this module. Accepting a Python
expression would be `exec` with a friendly name, and the whole point of a
declarative rule is that the set of things it can do is enumerable.

Computed on pandas, which TEE already has. The heavier engines the owner
named (Jesse, NautilusTrader) run in their OWN interpreters when present -
Jesse pins `mcp==1.28.1` against TEE's `mcp>=2`, and NautilusTrader needs
Python 3.12 while TEE is 3.11 - so `trade_probe` reports them rather than
this module importing them.
"""

from __future__ import annotations

import math
import time
from typing import Any

from tee.fleet.probe import have, need
from tee.kernel.errors import TeeError

RULES = ("sma_cross", "threshold", "buy_hold")
DEFAULT_PERIODS = 252
_STORE: dict[str, dict[str, Any]] = {}
_STORE_CAP = 16
_SEQ = [0]

NOT_ADVICE = (
    "A backtest over the series supplied. Past behaviour of a rule on a "
    "sample is not a prediction, and this is not investment advice."
)


def _remember(payload: dict[str, Any]) -> str:
    _SEQ[0] += 1
    rid = f"bt_{_SEQ[0]}"
    _STORE[rid] = payload
    while len(_STORE) > _STORE_CAP:
        _STORE.pop(next(iter(_STORE)))
    return rid


def _prices(spec: dict[str, Any]):
    pd = need("pandas", "quant", what="the dataframe layer")
    raw = spec.get("prices")
    if not isinstance(raw, list) or len(raw) < 30:
        raise TeeError(
            "trade_bad_spec",
            "prices must be a list of at least 30 numbers, oldest first.",
            fix="prices: [100.0, 100.5, 99.8, ...] - one instrument per backtest.",
        )
    try:
        s = pd.Series([float(x) for x in raw])
    except (TypeError, ValueError) as exc:
        raise TeeError(
            "trade_bad_spec", "prices must all be numbers.", fix="Strip nulls first."
        ) from exc
    if (s <= 0).any():
        raise TeeError(
            "trade_bad_spec",
            "prices must be positive.",
            fix="Returns are computed as ratios; a zero or negative price is undefined.",
        )
    return s


def _signal(prices, rule: dict[str, Any]):
    """Declarative rules only. -> a 0/1 position series, shifted so a
    signal formed on bar t is acted on at t+1 (no look-ahead)."""
    kind = str(rule.get("kind") or "sma_cross").lower()
    if kind not in RULES:
        raise TeeError(
            "trade_bad_rule",
            f"'{kind}' is not a rule.",
            fix=f"Use one of: {', '.join(RULES)}. Rules are declarative on "
            f"purpose - TEE does not evaluate caller-supplied code.",
        )
    if kind == "buy_hold":
        pos = prices * 0 + 1
    elif kind == "sma_cross":
        fast = int(rule.get("fast") or 20)
        slow = int(rule.get("slow") or 50)
        if fast >= slow:
            raise TeeError(
                "trade_bad_rule",
                f"fast ({fast}) must be shorter than slow ({slow}).",
                fix="A crossover needs two different windows.",
            )
        if slow >= len(prices):
            raise TeeError(
                "trade_bad_rule",
                f"slow window ({slow}) needs more than {len(prices)} observations.",
                fix="Supply a longer series or shorten the window.",
            )
        pos = (prices.rolling(fast).mean() > prices.rolling(slow).mean()).astype(float)
    else:  # threshold
        look = int(rule.get("lookback") or 20)
        up = float(rule.get("enter") or 0.0)
        mom = prices.pct_change(look)
        pos = (mom > up).astype(float)
    # act on the NEXT bar: a rule that trades on the bar that formed it is
    # trading on information it did not have.
    return pos.shift(1).fillna(0.0)


def backtest(spec: dict[str, Any]) -> dict[str, Any]:
    prices = _prices(spec)
    rule = dict(spec.get("rule") or {"kind": "sma_cross"})
    fee_bps = float(spec.get("fee_bps") or 0.0)
    periods = int(spec.get("periods_per_year") or DEFAULT_PERIODS)
    rf = float(spec.get("risk_free_rate") or 0.0)
    started = time.monotonic()

    pos = _signal(prices, rule)
    rets = prices.pct_change().fillna(0.0)
    turnover = pos.diff().abs().fillna(pos.abs())
    cost = turnover * (fee_bps / 10_000.0)
    strat = pos * rets - cost

    equity = (1.0 + strat).cumprod()
    total = float(equity.iloc[-1]) - 1.0
    years = len(prices) / periods
    cagr = (float(equity.iloc[-1]) ** (1 / years) - 1.0) if years > 0 else 0.0
    peak = equity.cummax()
    dd = equity / peak - 1.0
    max_dd = float(dd.min())
    vol = float(strat.std(ddof=1)) * math.sqrt(periods)
    mean = float(strat.mean()) * periods
    sharpe = ((mean - rf) / vol) if vol else None
    trades = int((turnover > 0).sum())
    wins = int((strat[strat != 0] > 0).sum())
    active = int((strat != 0).sum())

    rid = _remember(
        {
            "equity": [round(float(x), 6) for x in equity.tolist()],
            "position": [int(x) for x in pos.tolist()],
            "rule": rule,
            "n": len(prices),
        }
    )
    out = {
        "ok": True,
        "rule": rule,
        "n_observations": len(prices),
        "total_return": round(total, 6),
        "cagr": round(cagr, 6),
        "max_drawdown": round(max_dd, 6),
        "volatility": round(vol, 6),
        "sharpe": round(sharpe, 6) if sharpe is not None else None,
        "trades": trades,
        "win_rate": round(wins / active, 4) if active else None,
        "exposure": round(float((pos > 0).mean()), 4),
        "fee_bps": fee_bps,
        "run_id": rid,
        "wall_s": round(time.monotonic() - started, 4),
        "basis": f"annualised over {periods} periods, risk_free_rate={rf}; "
        f"signal acted on the bar AFTER it formed (no look-ahead)",
        "note": NOT_ADVICE,
    }
    if spec.get("compare_buy_hold", True):
        bh = (1.0 + rets).cumprod()
        out["buy_hold_return"] = round(float(bh.iloc[-1]) - 1.0, 6)
    return out


def detail(run_id: str, points: int = 40) -> dict[str, Any]:
    """The equity curve, RESAMPLED - not paged. A 5,000-bar curve served in
    pages of 500 is ten answers nobody wanted; forty points is the shape of
    the thing."""
    payload = _STORE.get(str(run_id))
    if payload is None:
        raise TeeError(
            "trade_unknown_run",
            f"No backtest '{run_id}' in this session.",
            fix=f"Known: {', '.join(_STORE) or '(none yet)'}. Re-run trade_backtest.",
        )
    eq = payload["equity"]
    points = max(5, min(int(points), 200))
    if len(eq) <= points:
        curve = eq
        idx = list(range(len(eq)))
    else:
        step = (len(eq) - 1) / (points - 1)
        idx = [round(i * step) for i in range(points)]
        curve = [eq[i] for i in idx]
    return {
        "run_id": run_id,
        "rule": payload["rule"],
        "n_observations": payload["n"],
        "points": len(curve),
        "at": idx,
        "equity": curve,
        "note": "resampled, not paged - the shape is the answer",
    }


def probe() -> dict[str, Any]:
    """What is available, and what TEE deliberately does not wire."""
    sidecars = {
        "jesse": {
            "installed_in_tee": have("jesse"),
            "why_not_in_tee": "pins mcp==1.28.1 against TEE's mcp>=2; needs its own venv",
            "licence": "MIT",
            "research_entrypoint": "jesse.research.backtest() - runs headless, "
            "no Postgres or Redis needed",
        },
        "nautilus_trader": {
            "installed_in_tee": have("nautilus_trader"),
            "why_not_in_tee": "requires Python >=3.12; TEE runs 3.11",
            "licence": "LGPL-3.0-only",
            "research_entrypoint": "nautilus_trader.backtest.BacktestEngine",
        },
        "hummingbot": {
            "installed_in_tee": False,
            "why_not_in_tee": "it exists to place orders continuously - there is no "
            "read-only shape of it worth wiring",
            "licence": "Apache-2.0",
            "research_entrypoint": None,
        },
        "openalgo": {
            "installed_in_tee": False,
            "why_not_in_tee": "one API key serves both reads and /analyzer/toggle, "
            "which flips simulated mode to live - so TEE holds no key at all",
            "licence": "AGPL-3.0-only",
            "research_entrypoint": None,
        },
    }
    return {
        "native_backtest": {
            "available": have("pandas"),
            "rules": list(RULES),
            "fix": None if have("pandas") else "uv pip install 'tee-engine[quant]'",
        },
        "sidecars": sidecars,
        "never_built": [
            "placing, amending or cancelling an order",
            "moving funds",
            "starting or stopping a live strategy",
            "toggling simulated/live mode",
            "reading a live broker account (the credential is the hazard)",
        ],
        "why": "TEE is driven by a model. Order placement is a decision a "
        "human takes in their broker's own interface, so the guard is "
        "ABSENCE - no such tool exists to be called, argued with or retried.",
    }
