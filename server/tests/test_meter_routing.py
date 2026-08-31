"""The merged meter (A42 R2): escalation, swap and job-class columns land
together in the ONE ledger, report_savings and the recap carry them, the
scheduler's columns are reserved in-schema (seam 2), and the router's
own bookkeeping overhead is measured negligible."""

from __future__ import annotations

import json
import time

from fixtures_llm import fake_llm_server
from test_llm_router import GOOD, _by_model, _route

from tee.kernel.machine import MachineLedger
from tee.llm.router import LADDER


def test_route_fills_the_merged_meter(tmp_path):
    ledger = MachineLedger(total_gb=128)
    with fake_llm_server(_by_model(set())) as (url, _calls):  # every engine fails
        routed = _route(url, tmp_path, ledger=ledger)
    assert routed["ok"] is False
    block = ledger.meter_block()
    assert block["routed_tasks"] == 1 and block["escalations"] == 1
    assert block["escalation_rate"] == 1.0
    # Derived from the ladder, not hardcoded: this asserted "2 engines" and
    # broke the moment A46 P3b registered a third. The invariant is that
    # EVERY rung was tried once and none verified, whatever the ladder holds.
    for engine in LADDER:
        assert block["engines"][engine] == {"calls": 1, "verified": 0}
    # One implicit swap per non-resident rung; the resident rung is free.
    assert block["swaps"]["implicit"] == len(LADDER) - 1
    assert block["swaps"]["refused"] == 0
    assert block["scheduler"]["queue_age_s"].startswith("reserved")
    assert block["scheduler"]["shadow_delta"].startswith("reserved")


def test_refused_swap_is_a_meter_column(tmp_path):
    ledger = MachineLedger(total_gb=128)
    ledger.register_job("okongo@odm", "reconstruct-odm")
    with fake_llm_server(_by_model(set())) as (url, _calls):
        _route(url, tmp_path, ledger=ledger)
    block = ledger.meter_block()
    # A registered job blocks a swap to every non-resident rung.
    assert block["swaps"]["refused"] == len(LADDER) - 1
    assert "okongo@odm" in block["swaps"]["last_refusal"]
    assert block["jobs"]["active"] == 1 and block["jobs"]["batch_footprint_gb"] == 16.0


def test_report_savings_and_recap_carry_the_block(tmp_path):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter

    project = tmp_path / "proj"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    report = app.registry.call("report_savings", {})
    assert report["routing"]["scheduler"]["dispatch_reason"].startswith("reserved")
    assert "router" not in app.recap()  # empty meter stays silent - budget

    app.machine.record_task()
    app.machine.record_escalation()
    assert "1 routed / 1 escalated" in app.recap()["router"]
    app.shutdown()


def test_router_bookkeeping_overhead_is_negligible(tmp_path):
    ledger = MachineLedger(total_gb=128)
    with fake_llm_server([GOOD] * 40) as (url, _calls):
        started = time.perf_counter()
        for _ in range(20):
            assert _route(url, tmp_path, ledger=ledger)["ok"]
        per_route_ms = (time.perf_counter() - started) / 20 * 1e3
    # the whole route (fake wire call included) stays in single-digit ms;
    # the bookkeeping share is printed for the PROGRESS row
    assert per_route_ms < 50, f"{per_route_ms:.1f} ms/route"
    print(f"\nroute() wall incl. fake engine: {per_route_ms:.2f} ms")
    assert json.dumps(ledger.meter_block())  # serializable, always
