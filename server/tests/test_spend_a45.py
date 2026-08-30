"""A45 P1: the money meter. SI-B16 (spend) + SI-B18 (egress), closed."""

from __future__ import annotations

import inspect

import pytest

from tee.kernel import local_llm, spend


@pytest.fixture(autouse=True)
def _clean():
    spend.reset()
    yield
    spend.reset()


def _call(**kw):
    base = dict(
        profile="qmax",
        endpoint="127.0.0.1:4000",
        model="m",
        paid=True,
        tokens_in=68,
        tokens_out=33,
    )
    base.update(kw)
    return spend.PaidCall(**base)


def test_endpoint_never_carries_a_path_or_a_key():
    assert spend.endpoint_of("http://127.0.0.1:4000/v1") == "127.0.0.1:4000"
    got = spend.endpoint_of("https://api.example.com/v1/chat?api_key=SECRET")
    assert got == "api.example.com"
    assert "SECRET" not in got


def test_only_paid_calls_count_as_having_left_the_machine():
    spend.record(_call(paid=True, tokens_in=68, bytes_sent=400))
    spend.record(_call(profile="q14b", paid=False, tokens_in=9000, bytes_sent=40000))
    s = spend.summary()
    assert s["sent"]["tokens"] == 68, "a local engine is not egress"
    assert s["sent"]["bytes"] == 400
    assert s["sent"]["off_machine_calls"] == 1
    assert s["sent"]["endpoints"] == ["127.0.0.1:4000"]
    # ...but the local engine is still shown, so the row is not simply absent
    assert s["engines"]["q14b"]["tokens_sent"] == 9000


def test_a_local_only_session_reads_a_clean_zero():
    spend.record(_call(profile="q14b", paid=False, tokens_in=500, bytes_sent=2000))
    s = spend.summary()
    assert s["sent"] == {
        "off_machine_calls": 0,
        "tokens": 0,
        "bytes": 0,
        "endpoints": [],
    }
    assert "estimated_cost" not in s


def test_no_rate_declared_means_no_invented_price():
    spend.record(_call())
    s = spend.summary()
    assert "estimated_cost" not in s
    assert s["cost_unavailable_for"] == ["qmax"]
    assert "price_in_per_mtok" in s["cost_fix"]


def test_declared_rate_prices_the_provider_reported_usage():
    spend.record(
        _call(
            tokens_in=1_000_000,
            tokens_out=1_000_000,
            price_in_per_mtok=2.0,
            price_out_per_mtok=8.0,
            currency="USD",
            price_source="owner",
        )
    )
    s = spend.summary()
    assert s["estimated_cost"]["USD"]["estimated_cost"] == pytest.approx(10.0)
    assert s["estimated_cost"]["USD"]["sources"] == ["owner"]
    assert "ESTIMATE" in s["cost_note"] and "Not a bill" in s["cost_note"]


def test_reasoning_tokens_are_surfaced_as_billed_but_unseen():
    spend.record(_call(reasoning_tokens=29))
    s = spend.summary()
    assert s["billed_but_unseen_tokens"] == 29
    assert "never saw" in s["billed_but_unseen_note"]


def test_usage_reader_handles_the_real_shape_this_machine_returned():
    payload = {
        "usage": {
            "prompt_tokens": 68,
            "completion_tokens": 33,
            "total_tokens": 101,
            "completion_tokens_details": {"reasoning_tokens": 29, "text_tokens": 33},
            "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 68},
        }
    }
    u = spend.usage_from_payload(payload)
    assert u == {
        "tokens_in": 68,
        "tokens_out": 33,
        "reasoning_tokens": 29,
        "cached_tokens": 0,
    }


def test_usage_reader_survives_a_provider_that_reports_nothing():
    assert spend.usage_from_payload({})["tokens_in"] == 0
    assert spend.usage_from_payload({"usage": None})["tokens_out"] == 0


def test_block_is_silent_until_an_engine_is_actually_called():
    assert spend.block() is None
    spend.record(_call())
    b = spend.block()
    assert b["off_machine_calls"] == 1
    assert b["estimated_cost"].startswith("no rate declared")


def test_ledger_is_bounded():
    for _ in range(spend._CAP + 50):
        spend.record(_call())
    assert len(spend.LEDGER) == spend._CAP


# -- the wiring, not just the arithmetic ------------------------------------


def test_the_llm_client_exposes_a_usage_hook():
    for fn in (local_llm.complete, local_llm.complete_json):
        assert "on_usage" in inspect.signature(fn).parameters


def test_the_chore_path_passes_the_hook():
    src = inspect.getsource(__import__("tee.llm.chores", fromlist=["x"]))
    assert "on_usage=_meter" in src, "chores must meter the call it makes"
    assert "spend.PaidCall" in src


def test_metering_never_breaks_the_chore_it_measures(monkeypatch):
    """A meter that raises must not take the answer down with it."""
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise RuntimeError("meter exploded")

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b""

    payload = {"choices": [{"message": {"content": "hello"}}], "usage": {}}
    monkeypatch.setattr(local_llm.json, "load", lambda r: payload)
    monkeypatch.setattr(local_llm.urllib.request, "urlopen", lambda *a, **k: FakeResp())
    text = local_llm.complete("hi", url="http://x/v1", model="m", on_usage=boom)
    assert text == "hello"
    assert calls["n"] == 1, "the hook was called and its failure was swallowed"
