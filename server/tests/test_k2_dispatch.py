"""K2 (A42): the greedy dispatch behind its replay gate. The replay
report's math both ways, the policy actually reordering the ladder from
the measured tables (the R2 constants flip resident-27B cases to a 14B
load), the pin outranking every policy, and the dispatch_reason column
filling in the meter."""

from __future__ import annotations

import json

from fixtures_llm import fake_llm_server
from test_llm_router import _by_model, _cfg

from tee.kernel import shadow
from tee.kernel.machine import MachineLedger
from tee.llm import chores, router

TB = "Traceback: AttributeError: 'NoneType' object has no attribute 'free'"
EV = "line 2: bm = existing.get(name)"


def _trace_line(engine, shadow_engine, wall, estimate, agrees):
    return {
        "ts": 0,
        "task": {"id": "chore:triage", "kind": "chore", "engine": engine},
        "actual": {"outcome": "verified", "wall_s": wall},
        "shadow": {"engine": shadow_engine, "estimate_s": estimate},
        "delta": {"agrees": agrees, "est_minus_actual_s": round(estimate - wall, 2)},
    }


def _write_traces(directory, lines):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "traces-20260829.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")


def test_replay_passes_on_agreement(tmp_path):
    _write_traces(tmp_path, [_trace_line("q14b+a2", "q14b+a2", 1.3, 1.24, True)] * 9
                  + [_trace_line("q27b-bare", "q14b+a2", 7.0, 2.3, False)])  # fmt: skip
    report = shadow.replay([tmp_path])
    assert report["chore_dispatches"] == 10
    assert report["agreement_rate"] == 0.9
    assert report["passes"] is True
    assert report["estimate_mae_s"] is not None


def test_replay_passes_when_every_disagreement_is_greedy_better(tmp_path):
    _write_traces(tmp_path, [_trace_line("q27b-bare", "q14b+a2", 7.0, 2.3, False)] * 4)
    report = shadow.replay([tmp_path])
    assert report["agreement_rate"] == 0.0
    assert report["passes"] is True  # greedy better by estimate on every one
    assert all(d["greedy_better_by_estimate"] for d in report["disagreements"])


def test_replay_fails_on_mixed_disagreement(tmp_path):
    _write_traces(tmp_path, [
        _trace_line("q14b+a2", "q27b-bare", 1.0, 8.0, False),  # greedy would be WORSE
        _trace_line("q27b-bare", "q14b+a2", 7.0, 2.3, False),
        _trace_line("q14b+a2", "q14b+a2", 1.3, 1.24, True),
    ])  # fmt: skip
    report = shadow.replay([tmp_path])
    assert report["passes"] is False


def _call(cfg):
    return chores.triage(TB, EV, refine="local", cfg=cfg)


def test_greedy_policy_reorders_the_ladder(tmp_path):
    # persisted resident = q27b; the measured swap constants say load the 14B
    (tmp_path / "llm-profile.json").write_text(json.dumps({"active": "q27b", "ready": True}))
    ledger = MachineLedger(total_gb=128)
    with fake_llm_server(_by_model({"fake-14b"})) as (url, calls):
        routed = router.route(
            "triage", _call, cfg=_cfg(url, tmp_path), ledger=ledger,
            input_pointer="x", policy="greedy",
        )  # fmt: skip
    assert routed["ok"] and routed["engine"] == "q14b+a2"
    assert calls[0]["model"] == "fake-14b"  # greedy went straight to the 14B
    block = ledger.meter_block()
    assert block["swaps"]["implicit"] == 1  # the load was counted
    assert block["scheduler"]["dispatch_reason"]["greedy"] == 1
    assert "greedy" in block["scheduler"]["dispatch_reason"]["last"]


def test_static_policy_stays_resident_first(tmp_path):
    (tmp_path / "llm-profile.json").write_text(json.dumps({"active": "q27b", "ready": True}))
    with fake_llm_server(_by_model({"fake-27b"})) as (url, calls):
        routed = router.route(
            "triage", _call, cfg=_cfg(url, tmp_path),
            ledger=MachineLedger(total_gb=128), input_pointer="x",
        )  # fmt: skip
    assert routed["ok"] and routed["engine"] == "q27b-bare"
    assert calls[0]["model"] == "fake-27b"


def test_pin_outranks_greedy(tmp_path):
    (tmp_path / "llm-profile.json").write_text(
        json.dumps({"active": "q27b", "ready": True, "pinned": True})
    )
    ledger = MachineLedger(total_gb=128)
    with fake_llm_server(_by_model({"fake-27b"})) as (url, calls):
        routed = router.route(
            "triage", _call, cfg=_cfg(url, tmp_path), ledger=ledger,
            input_pointer="x", policy="greedy",
        )  # fmt: skip
    assert routed["ok"] and routed["engine"] == "q27b-bare"
    assert {c["model"] for c in calls} == {"fake-27b"}
    assert ledger.meter_block()["scheduler"]["dispatch_reason"]["pinned"] == 1


def test_dispatch_defaults_on_after_the_replay_gate(tmp_path):
    # K2 went live 2026-08-29: the binding replay passed (every
    # disagreement greedy-better-by-estimate), so greedy is the default
    # and [scheduler] dispatch = false restores static.
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter

    project = tmp_path / "proj"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    scheduler_cfg = dict(app.config.scheduler or {})
    assert scheduler_cfg.get("dispatch", True) is True
    app.shutdown()
