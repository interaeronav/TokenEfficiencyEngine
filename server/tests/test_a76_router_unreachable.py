"""A76 P0: an unreachable endpoint is not a verification failure.

`router.route` catches every `TeeError` from the engine call in one arm and
records `record_route(engine, verified=False)` — so `llm_unreachable` (nothing
was listening) and a genuine verifier kill (the model answered and the chore's
own validator rejected it) increment the same counter. Doc 55 designates
`escalation_rate` the quality alarm; on a machine whose backend is down it is
measuring the network instead.

A46 P3b fixed exactly this shape for a DIFFERENT cause — a profile the machine
has not declared is recorded as `skipped`, not as a failure, with a comment at
router.py:113-119 saying "Registering an engine centrally must not defame it on
machines that do not serve it." The same sentence applies to an engine whose
endpoint is dead, and the code does not yet say so.

**These tests FAIL until P3 lands the split.** That is deliberate: P0's
acceptance is that the defect is reproduced before it is fixed.
"""

from __future__ import annotations

import socket

import pytest
from fixtures_llm import fake_llm_server
from test_llm_router import GOOD, _by_model, _call, _cfg

from tee.kernel.machine import MachineLedger
from tee.llm import router


def _dead_port() -> int:
    """A port nothing is listening on: bind it, learn it, release it."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _route_to_nothing(tmp_path, ledger):
    return router.route(
        "triage",
        _call,
        cfg=_cfg(f"http://127.0.0.1:{_dead_port()}/v1", tmp_path),
        ledger=ledger,
        input_pointer="job7/traceback",
    )


def test_every_rung_is_attempted_and_the_task_escalates(tmp_path):
    """The part that already works, pinned so the fix cannot regress it."""
    ledger = MachineLedger(total_gb=128)
    routed = _route_to_nothing(tmp_path, ledger)
    assert not routed["ok"], "nothing is listening; the task must escalate"
    assert routed["escalate"], "an escalation carries a client brief"
    assert len(routed["hops"]) == len(router.LADDER), routed["hops"]
    assert ledger.meter_block()["escalations"] == 1


@pytest.mark.xfail(
    reason="A76 P0: the defect, reproduced. Passes when P3 lands the split.",
    strict=True,
)
def test_an_unreachable_endpoint_is_not_counted_as_a_failed_verification(tmp_path):
    ledger = MachineLedger(total_gb=128)
    _route_to_nothing(tmp_path, ledger)
    engines = ledger.meter_block()["engines"]
    assert engines, "the hops were recorded against some engine"
    for name, row in engines.items():
        assert row.get("unreachable", 0) >= 1, (
            f"{name}: an endpoint that never answered must be recorded as "
            f"unreachable, not as a verification failure; got {row}"
        )
        assert row["calls"] == 0, (
            f"{name}: nothing answered, so nothing was verified or falsified; "
            f"counting it as a call defames an engine that was never asked. "
            f"Got {row}"
        )


@pytest.mark.xfail(
    reason="A76 P0: the defect, reproduced. Passes when P3 lands the split.",
    strict=True,
)
def test_the_meter_can_attribute_an_escalation_to_the_network(tmp_path):
    """doc 55 calls escalation_rate the quality alarm. It cannot be one while a
    dead port and a bad answer are the same number."""
    ledger = MachineLedger(total_gb=128)
    _route_to_nothing(tmp_path, ledger)
    block = ledger.meter_block()
    assert block["escalations"] == 1
    assert block.get("unreachable_hops", 0) == len(router.LADDER), (
        "the meter cannot say whether this escalation was the models failing "
        f"or the machine being down: {block}"
    )


def test_a_real_verifier_kill_is_still_a_verification_failure(tmp_path):
    """The other half of the split: when the engine DOES answer and the chore's
    validator rejects it, that must stay a verification failure. The fix must
    not launder genuine failures into 'unreachable'."""
    ledger = MachineLedger(total_gb=128)
    with fake_llm_server(_by_model(set())) as (url, _calls):  # every model answers badly
        routed = router.route(
            "triage",
            _call,
            cfg=_cfg(url, tmp_path),
            ledger=ledger,
            input_pointer="job7/traceback",
        )
    assert not routed["ok"]
    assert all(h.get("verdict") == "llm_bad_shape" for h in routed["hops"]), routed["hops"]
    engines = ledger.meter_block()["engines"]
    for name, row in engines.items():
        assert row["calls"] >= 1, f"{name} answered; it must be counted as asked"
        assert row["verified"] == 0, f"{name} answered badly; it must not count as verified"
        assert row.get("unreachable", 0) == 0, (
            f"{name}: the model answered — this is a verification failure, "
            f"not a network failure. Got {row}"
        )


def test_the_two_causes_are_currently_indistinguishable(tmp_path):
    """The defect stated as a passing test, so the record shows what was true.

    Delete this test when P3 lands: it asserts the bug.
    """
    dead, bad = MachineLedger(total_gb=128), MachineLedger(total_gb=128)
    _route_to_nothing(tmp_path, dead)
    with fake_llm_server(_by_model(set())) as (url, _c):
        router.route("triage", _call, cfg=_cfg(url, tmp_path), ledger=bad,
                     input_pointer="job7/traceback")
    shape = lambda b: {n: dict(r) for n, r in b.meter_block()["engines"].items()}  # noqa: E731
    assert shape(dead) == shape(bad), (
        "if these ever differ, the split has landed and this test should go"
    )
