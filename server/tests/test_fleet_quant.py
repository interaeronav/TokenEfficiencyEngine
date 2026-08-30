"""A45 P2b — portfolio optimisation.

The load-bearing invariant is not "it ran": it is that each method wins on
its own metric when every method is measured on the SAME basis. That only
became true after TEE stopped trusting each library's own
`portfolio_performance` - see the uniform-basis test below.
"""

from __future__ import annotations

import tempfile

import pytest

from tee.fleet import probe, quant
from tee.kernel.errors import TeeError

needs_quant = pytest.mark.skipif(
    not (probe.have("pypfopt") and probe.have("skfolio") and probe.have("pandas")),
    reason="[quant] extra not installed",
)


def _series(n: int = 260):
    """DETERMINISTIC three-asset set - no RNG, on purpose.

    A random fixture made this suite's meaning depend on the draw: with
    `default_rng(7)` all three sample means came out NEGATIVE despite
    positive parameters, because over 250 observations the standard error
    of the mean (sd/sqrt(n)) is about twice the drift. The test then
    asserted a property the data did not contain.

    Sine noise averages to ~0 over whole periods, so each asset's realised
    mean IS its drift. By construction SAFE has the best risk-adjusted
    profile and WILD the worst, which is what the assertions rely on.
    """
    import math

    def series(drift: float, amp: float, freq: float):
        return [drift + amp * math.sin(freq * t) for t in range(n)]

    return {
        "SAFE": series(0.0006, 0.004, 0.7),
        "MID": series(0.0009, 0.012, 1.1),
        "WILD": series(0.0011, 0.030, 1.9),
    }


def _flat_series(n: int = 260):
    """A sample where nothing clears a normal hurdle - the common real case."""
    import math

    return {
        "A": [-0.0001 + 0.005 * math.sin(0.9 * t) for t in range(n)],
        "B": [-0.0002 + 0.011 * math.sin(1.4 * t) for t in range(n)],
    }


@needs_quant
@pytest.mark.parametrize("method", ["max_sharpe", "min_volatility", "hrp", "mean_risk"])
def test_every_method_returns_weights_that_sum_to_one(method):
    r = quant.optimize({"returns": _series(), "method": method})
    assert r["ok"] is True
    assert r["weights_sum"] == pytest.approx(1.0, abs=1e-4)
    assert all(v >= -1e-6 for v in r["weights"].values()), "long-only by default"


@needs_quant
def test_each_method_wins_on_its_own_metric_because_the_basis_is_shared():
    """The bug this pins. PyPortfolioOpt's HRPOpt.portfolio_performance
    defaults to risk_free_rate=0 and an arithmetic mean, while
    EfficientFrontier reports against the GEOMETRIC mu it optimised on with
    rf=0.02. Measured before the fix: hrp appeared to score Sharpe 0.514
    against max_sharpe's 0.255 - a units mismatch masquerading as a result.
    TEE now computes all metrics itself, on one basis."""
    s = _series()
    res = {m: quant.optimize({"returns": s, "method": m}) for m in quant.METHODS}
    best_sharpe = max(res.values(), key=lambda r: r["sharpe"])
    assert best_sharpe["method"] == "max_sharpe", {m: r["sharpe"] for m, r in res.items()}
    lowest_vol = min(res.values(), key=lambda r: r["volatility"])
    assert lowest_vol["method"] in ("min_volatility", "mean_risk"), {
        m: r["volatility"] for m, r in res.items()
    }


@needs_quant
def test_the_basis_is_stated_in_the_payload():
    r = quant.optimize({"returns": _series(), "method": "max_sharpe"})
    assert "annualised over 252 periods" in r["basis"]
    assert "risk_free_rate=0.02" in r["basis"]
    assert "comparable" in r["basis"]


@needs_quant
def test_changing_the_risk_free_rate_moves_sharpe_the_right_way():
    s = _series()
    lo = quant.optimize({"returns": s, "method": "min_volatility", "risk_free_rate": 0.0})
    hi = quant.optimize({"returns": s, "method": "min_volatility", "risk_free_rate": 0.10})
    assert lo["sharpe"] > hi["sharpe"], "a higher hurdle must lower the ratio"


@needs_quant
def test_prices_and_returns_inputs_agree():
    rets = _series(300)
    prices = {}
    for k, v in rets.items():
        p, out = 100.0, []
        for x in v:
            p *= 1 + x
            out.append(p)
        prices[k] = out
    a = quant.optimize({"returns": rets, "method": "min_volatility"})
    b = quant.optimize({"prices": prices, "method": "min_volatility"})
    for k in a["weights"]:
        assert b["weights"][k] == pytest.approx(a["weights"][k], abs=0.02), k


# -- token discipline -------------------------------------------------------


@needs_quant
def test_a_large_universe_is_summarised_not_dumped():
    import math

    universe = {
        f"A{i:03d}": [0.0004 + 0.01 * math.sin((0.5 + i * 0.03) * t) for t in range(260)]
        for i in range(120)
    }
    r = quant.optimize({"returns": universe, "method": "hrp"})
    assert r["n_assets"] == 120
    assert len(r["weights"]) <= quant.DEFAULT_SHOW
    assert "quant_detail" in r["truncated"]
    full = quant.detail(r["weights_id"], limit=1000)
    assert full["total"] == 120
    assert sum(full["weights"].values()) == pytest.approx(1.0, abs=1e-4)


@needs_quant
def test_the_payload_says_it_is_not_advice():
    r = quant.optimize({"returns": _series(), "method": "max_sharpe"})
    assert "not investment advice" in r["note"]
    d = quant.detail(r["weights_id"])
    assert "not investment advice" in d["note"]


# -- refusals ---------------------------------------------------------------


def test_unknown_weights_id_refuses():
    with pytest.raises(TeeError) as e:
        quant.detail("w_nope")
    assert "No weights" in e.value.message


@needs_quant
def test_bad_inputs_refuse_with_a_fix():
    with pytest.raises(TeeError) as e:
        quant.optimize({"returns": _series(), "method": "moon"})
    assert "max_sharpe" in e.value.fix

    with pytest.raises(TeeError) as e:
        quant.optimize({"method": "max_sharpe"})
    assert "prices" in e.value.fix

    with pytest.raises(TeeError) as e:
        quant.optimize({"returns": {"A": [0.1] * 30, "B": [0.1] * 25}})
    assert "different lengths" in e.value.message

    with pytest.raises(TeeError) as e:
        quant.optimize({"returns": {"A": [0.1] * 5, "B": [0.1] * 5}})
    assert "too few" in e.value.message


@needs_quant
def test_a_hurdle_no_asset_can_clear_refuses_instead_of_raising_valueerror():
    """PyPortfolioOpt raises a bare ValueError when nothing beats the
    risk-free rate. Found by a test whose random draw happened to produce
    exactly that - a common case in a flat sample, not an edge."""
    with pytest.raises(TeeError) as e:
        quant.optimize({"returns": _flat_series(), "method": "max_sharpe"})
    assert e.value.code == "quant_no_asset_beats_rf"
    assert "min_volatility" in e.value.fix


def test_missing_extra_refuses_with_the_command():
    with pytest.raises(TeeError) as e:
        probe.need("pypfopt_not_here", "quant")
    assert "tee-engine[quant]" in e.value.fix


def test_tools_register_on_read_compute():
    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    for name in ("quant_optimize", "quant_detail", "quant_backends"):
        assert app.registry._tools[name].capability == "read-compute"
