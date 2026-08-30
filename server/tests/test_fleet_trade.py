"""A45 P2f — trading research.

Two things are being tested and only one is arithmetic. The first is that
the backtest is CORRECT - no look-ahead, fees bite, trend rules behave like
trend rules. The second is that the dangerous half is ABSENT: no tool
exists that could place an order, and none can be added by accident.
"""

from __future__ import annotations

import math
import re
import tempfile

import pytest

from tee.fleet import probe, trade
from tee.kernel.errors import TeeError

needs_pandas = pytest.mark.skipif(not probe.have("pandas"), reason="pandas not installed")


def _series(n: int = 400, turn: int = 200):
    """Deterministic: rises for `turn` bars, then falls. A trend rule should
    capture the rise and sit out the fall; buy-and-hold cannot."""
    out, p = [], 100.0
    for t in range(n):
        drift = 0.004 if t < turn else -0.003
        p *= 1 + drift + 0.006 * math.sin(t * 0.8)
        out.append(p)
    return out


# -- correctness ------------------------------------------------------------


@needs_pandas
def test_no_look_ahead_the_future_cannot_change_the_past():
    """The property that separates a backtest from a fantasy. Changing the
    LAST bar must not alter the equity curve before it."""
    prices = _series()
    a = trade.backtest({"prices": prices, "rule": {"kind": "sma_cross", "fast": 10, "slow": 40}})
    bumped = list(prices)
    bumped[-1] *= 3.0  # a wild final bar
    b = trade.backtest({"prices": bumped, "rule": {"kind": "sma_cross", "fast": 10, "slow": 40}})
    ca = trade.detail(a["run_id"], points=200)["equity"]
    cb = trade.detail(b["run_id"], points=200)["equity"]
    assert ca[:-2] == pytest.approx(cb[:-2], rel=1e-9), "the past moved when the future changed"


@needs_pandas
def test_a_trend_rule_sits_out_the_downtrend_that_buy_and_hold_rides():
    prices = _series()
    bh = trade.backtest({"prices": prices, "rule": {"kind": "buy_hold"}})
    sma = trade.backtest({"prices": prices, "rule": {"kind": "sma_cross", "fast": 10, "slow": 40}})
    assert bh["max_drawdown"] < -0.30, "buy-and-hold must ride the reversal down"
    assert sma["max_drawdown"] > bh["max_drawdown"], "the trend rule must cut the drawdown"
    assert sma["exposure"] < 1.0, "it must be out of the market some of the time"
    # 399/400, not 1.0: the no-look-ahead shift means nothing can be held
    # on bar 0. That the "always in" rule is NOT 100% exposed is itself
    # evidence the shift is applied.
    assert bh["exposure"] == pytest.approx((len(prices) - 1) / len(prices), abs=1e-6)


@needs_pandas
def test_fees_reduce_the_return_monotonically():
    prices = _series()
    rule = {"kind": "sma_cross", "fast": 10, "slow": 40}
    free = trade.backtest({"prices": prices, "rule": rule, "fee_bps": 0})
    dear = trade.backtest({"prices": prices, "rule": rule, "fee_bps": 200})
    assert dear["total_return"] < free["total_return"]
    assert dear["trades"] == free["trades"], "fees change cost, not the signal"


@needs_pandas
def test_buy_hold_matches_the_series_itself():
    prices = _series()
    r = trade.backtest({"prices": prices, "rule": {"kind": "buy_hold"}, "fee_bps": 0})
    expected = prices[-1] / prices[0] - 1
    # buy_hold enters on bar 1 (the shift), so it misses the first bar's move
    assert r["total_return"] == pytest.approx(expected, rel=0.02)
    assert r["buy_hold_return"] == pytest.approx(expected, rel=0.02)


@needs_pandas
def test_the_basis_and_the_disclaimer_travel_with_the_answer():
    r = trade.backtest({"prices": _series(), "rule": {"kind": "buy_hold"}})
    assert "no look-ahead" in r["basis"]
    assert "not investment advice" in r["note"]


# -- token discipline -------------------------------------------------------


@needs_pandas
def test_detail_resamples_rather_than_pages():
    r = trade.backtest({"prices": _series(400), "rule": {"kind": "buy_hold"}})
    d = trade.detail(r["run_id"], points=20)
    assert d["points"] == 20
    assert d["n_observations"] == 400
    assert len(d["at"]) == 20
    assert "resampled, not paged" in d["note"]


@needs_pandas
def test_the_backtest_answer_never_carries_the_curve():
    r = trade.backtest({"prices": _series(2000), "rule": {"kind": "buy_hold"}})
    assert len(repr(r)) < 700, "headline metrics only"
    assert "equity" not in r


# -- refusals ---------------------------------------------------------------


@needs_pandas
def test_rules_are_declarative_and_code_is_not_a_rule():
    with pytest.raises(TeeError) as e:
        trade.backtest({"prices": _series(), "rule": {"kind": "__import__('os').system('id')"}})
    assert e.value.code == "trade_bad_rule"
    assert "declarative" in e.value.fix


@needs_pandas
def test_bad_inputs_refuse_with_a_fix():
    with pytest.raises(TeeError):
        trade.backtest({"prices": [1, 2, 3]})  # too short
    with pytest.raises(TeeError) as e:
        trade.backtest({"prices": [100.0] * 40 + [0.0]})
    assert "positive" in e.value.message
    with pytest.raises(TeeError) as e:
        trade.backtest({"prices": _series(), "rule": {"kind": "sma_cross", "fast": 50, "slow": 10}})
    assert "shorter" in e.value.message


def test_unknown_run_refuses():
    with pytest.raises(TeeError) as e:
        trade.detail("bt_nope")
    assert "No backtest" in e.value.message


# -- the guard is ABSENCE ---------------------------------------------------

_DANGEROUS = re.compile(
    r"place_?order|submit_?order|market_order|limit_order|cancel|amend|modify_?order"
    r"|withdraw|transfer|deposit|funds|balance|positionbook|analyzer",
    re.I,
)


def test_no_tool_in_the_whole_registry_has_an_order_shaped_name():
    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    offenders = [n for n in app.registry._tools if _DANGEROUS.search(n)]
    assert offenders == [], f"order-shaped tool names present: {offenders}"


def test_the_trade_module_contains_no_broker_call():
    """No HTTP client, no credential, no exchange SDK - asserted on source."""
    import pathlib

    src = pathlib.Path(trade.__file__).read_text()
    body = src.split('"""', 2)[-1]  # skip the module docstring, which discusses them
    for token in ("requests", "urllib.request", "httpx", "api_key", "apikey", "secret"):
        assert token not in body, f"{token} appears in the trade module body"


def test_untabled_trade_tools_cannot_boot():
    from tee.kernel import trust

    for name in ("trade_place_order", "trade_account", "trade_funds", "trade_cancel"):
        with pytest.raises(TeeError):
            trust.capability_for(name)


def test_probe_states_plainly_what_is_never_built():
    r = trade.probe()
    never = " ".join(r["never_built"]).lower()
    assert "placing" in never and "moving funds" in never
    assert "live broker account" in never
    assert r["sidecars"]["openalgo"]["installed_in_tee"] is False
    assert "analyzer/toggle" in r["sidecars"]["openalgo"]["why_not_in_tee"]
    assert "ABSENCE" in r["why"]


def test_registration_on_read_compute():
    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    for n in ("trade_backtest", "trade_detail", "trade_probe"):
        assert app.registry._tools[n].capability == "read-compute"
