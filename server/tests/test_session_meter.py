"""Savings meter + handoff pack (A37 P6 = A36 G3/G4).

The ledger arithmetic is fixture-tested, the naive baseline is a
LABELLED estimate priced by measured scenario ratios, the recap carries
the compact block, and the handoff brief holds its budget while keeping
the load-bearing facts."""

from __future__ import annotations

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import ResponseLog, estimate_tokens
from tee.kernel.meter import ESTIMATE_NOTE, MEASURED_RATIOS, lane_for, savings


def test_ledger_sums_and_excludes_virtual_rows_from_totals() -> None:
    log = ResponseLog()
    log.record("tee_status", {"ok": True}, request={"recap": True})
    log.record("tee_call", {"ok": True, "items": [1, 2, 3]}, request={"name": "kb_search"})
    log.record("virtual:kb_search", {"ok": True, "items": [1, 2, 3]})
    ledger = log.ledger()
    assert ledger["tools"]["tee_status"]["calls"] == 1
    assert ledger["tools"]["tee_status"]["tokens_in"] > 0
    # virtual rows detail tee_call traffic; totals stay wire-level
    wire_out = (
        ledger["tools"]["tee_status"]["tokens_out"] + ledger["tools"]["tee_call"]["tokens_out"]
    )
    assert ledger["totals"]["tokens_out"] == wire_out
    assert ledger["totals"]["calls"] == 2


def test_lane_mapping_covers_the_measured_scenarios() -> None:
    assert lane_for("tee_batch") == "scenes"
    assert lane_for("tee_web_lookup") == "web"
    assert lane_for("virtual:kb_search") == "kb"
    assert lane_for("virtual:ex_facts") == "extract"
    assert lane_for("virtual:as_search") == "assets"
    assert lane_for("virtual:fs.read_text_file") == "gateway"
    assert lane_for("tee_status") is None  # no honest baseline -> no estimate
    assert lane_for("virtual:llm_triage") is None


def test_savings_estimate_math_and_labelling() -> None:
    log = ResponseLog()
    log.record("tee_batch", {"created": ["e1"]}, request={"ops": [{"op": "create"}]})
    log.record("tee_status", {"ok": True}, request={})
    result = savings(log.ledger())
    lane = result["lanes"]["scenes"]
    ratio, source = MEASURED_RATIOS["scenes"]
    assert lane["naive_estimate"] == round(lane["tokens"] / (1 - ratio))
    assert lane["ratio_source"] == source
    assert result["note"] == ESTIMATE_NOTE  # the label IS the acceptance
    assert result["naive_estimate"] == lane["naive_estimate"]
    # measured totals include the unestimated tee_status row
    assert result["measured"]["calls"] == 2


def test_recap_carries_the_compact_savings_block(tmp_path) -> None:
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        assert "savings" not in app.recap()  # empty ledger: no block
        app.response_log.record("tee_batch", {"created": ["e1"]}, request={"ops": []})
        block = app.recap()["savings"]
        assert block["calls"] == 1 and block["tokens"] > 0
        assert "naive_estimate" in block and "report_savings" in block["note"]
    finally:
        app.shutdown()


def test_report_savings_and_handoff_are_registered_virtual(tmp_path) -> None:
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        names = app.registry.names()
        assert "report_savings" in names and "handoff" in names
        hits = app.registry.search("portable brief resume")
        assert hits["items"][0]["name"] == "handoff"
        out = app.registry.call("report_savings", {})
        assert out["note"] == ESTIMATE_NOTE
    finally:
        app.shutdown()


def test_handoff_brief_holds_budget_and_load_bearing_facts(tmp_path) -> None:
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        app.run_batch("fake", [{"op": "create", "kind": "wall", "name": "w1"}], label="site")
        app.memory.remember("blender", "5.2 LTS")
        for i in range(40):  # enough notes to overflow an unbounded brief
            app.memory.note(f"note {i}: " + "detail " * 30)
        out = app.registry.call("handoff", {})
        brief = out["brief"]
        assert out["tokens"] <= out["budget"] == 500
        assert estimate_tokens(brief) <= 500
        assert brief.startswith("TEE HANDOFF")
        assert "fake: epoch" in brief and "wall x1" in brief  # scene stamp
        assert "blender=5.2 LTS" in brief  # facts survive the trim
        assert "tee_recall" in brief  # the continue-with-TEE pointer
    finally:
        app.shutdown()


def test_wire_level_requests_are_counted(tmp_path) -> None:
    import anyio
    from mcp.client import Client

    from tee.server import build_server

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        server = build_server(app)

        async def drive():
            async with Client(server) as client:
                await client.call_tool("tee_status", {"recap": True})

        anyio.run(drive)
        row = app.response_log.ledger()["tools"]["tee_status"]
        assert row["calls"] == 1 and row["tokens_in"] > 0 and row["tokens_out"] > 0
    finally:
        app.shutdown()
