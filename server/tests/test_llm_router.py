"""The verifier-gated cascade on fakes (A42 R1 acceptance): every hop
fixtured - first-engine pass, ladder escalation on a deterministic
verifier kill, the guard seam refusing the swap rung while a registered
job holds the machine, the never-swap memory rule, the owner's TEE/Q pin
suspending roaming, and the budgeted pointer-only client brief."""

from __future__ import annotations

import json

import pytest
from fixtures_llm import fake_llm_server

from tee.kernel.machine import MachineLedger
from tee.llm import chores, router

TRACEBACK = (
    "Traceback (most recent call last):\n"
    '  File "populate.py", line 6, in <module>\n'
    "TypeError: spawn_actor() got an unexpected keyword argument 'transform'"
)
EVIDENCE = "line 6: actor = world.spawn_actor(bp, transform=tf)"
GOOD = json.dumps(
    {"diagnosis": "The kwarg is not accepted.", "fix": "Pass a Transform object.",
     "confidence": "grounded"}
)  # fmt: skip


def _cfg(url: str, state_dir) -> dict:
    return {
        "url": url,
        "_state_dir": str(state_dir),
        # Every rung of the ladder, so a newly registered engine is
        # EXERCISED here rather than silently skipped as undeclared. When
        # A46 P3b added dsflash, an incomplete fixture would have quietly
        # dropped it out of every cascade test.
        "profiles": {
            "q14b": {"model": "fake-14b", "adapters": ""},
            "q27b": {"model": "fake-27b", "adapters": ""},
            "dsflash": {"model": "fake-dsflash", "adapters": ""},
        },
    }


def _call(cfg):
    return chores.triage(TRACEBACK, EVIDENCE, refine="local", cfg=cfg)


def _route(url, tmp_path, ledger=None):
    return router.route(
        "triage",
        _call,
        cfg=_cfg(url, tmp_path),
        ledger=ledger or MachineLedger(total_gb=128),
        input_pointer="job7/traceback",
    )


def _by_model(good_models: set[str]):
    def replies(request: dict) -> str:
        # bad = valid JSON, wrong shape -> the chore's own validate kills it
        return GOOD if request.get("model") in good_models else '{"wrong": "shape"}'

    return replies


def test_first_engine_verified_no_roaming(tmp_path):
    with fake_llm_server(_by_model({"fake-14b"})) as (url, calls):
        routed = _route(url, tmp_path)
    assert routed["ok"] and routed["engine"] == "q14b+a2"
    assert routed["hops"] == [{"engine": "q14b+a2", "verdict": "verified"}]
    assert routed["result"]["confidence"] == "grounded"
    assert all(c["model"] == "fake-14b" for c in calls)


def test_ladder_escalates_on_verifier_kill(tmp_path):
    with fake_llm_server(_by_model({"fake-27b"})) as (url, _calls):
        routed = _route(url, tmp_path)
    assert routed["ok"] and routed["engine"] == "q27b-bare"
    # Every rung above the winner fails the verifier and is escalated past.
    assert [h.get("verdict") for h in routed["hops"]] == [
        *["llm_bad_shape"] * (len(router.LADDER) - 1),
        "verified",
    ]


def test_guard_seam_swap_refused_during_registered_job(tmp_path):
    ledger = MachineLedger(total_gb=128)
    ledger.register_job("okongo@odm", "reconstruct-odm")
    with fake_llm_server(_by_model(set())) as (url, calls):  # every engine fails
        routed = _route(url, tmp_path, ledger=ledger)
    assert routed["ok"] is False
    skipped = [h for h in routed["hops"] if "skipped" in h]
    # One per non-resident rung: the held machine refuses every swap.
    assert len(skipped) == len(router.LADDER) - 1
    assert all("okongo@odm" in h["skipped"] for h in skipped)
    # the 27B rung was never called: only the 14B model reached the wire
    assert {c["model"] for c in calls} == {"fake-14b"}


def test_never_swap_when_memory_cannot_fit(tmp_path):
    ledger = MachineLedger(total_gb=32)  # 27B (55 GB) can never fit
    with fake_llm_server(_by_model(set())) as (url, _calls):
        routed = _route(url, tmp_path, ledger=ledger)
    skips = [h for h in routed["hops"] if "skipped" in h]
    skip = next(h for h in skips if h["engine"] == "q27b-bare")
    assert "55 GB" in skip["skipped"]


def test_owner_pin_suspends_roaming(tmp_path):
    (tmp_path / "llm-profile.json").write_text(
        json.dumps({"active": "q14b", "ready": True, "pinned": True})
    )
    with fake_llm_server(_by_model(set())) as (url, calls):
        routed = _route(url, tmp_path)
    assert routed["ok"] is False and routed["pinned"] is True
    assert len(routed["hops"]) == 1  # no rung beyond the pinned engine
    assert routed["escalate"]["note"].startswith("roaming suspended")
    assert {c["model"] for c in calls} == {"fake-14b"}


def test_client_brief_is_budgeted_and_pointer_only(tmp_path):
    with fake_llm_server(_by_model(set())) as (url, _calls):
        routed = _route(url, tmp_path)
    brief = routed["escalate"]
    assert brief["task"] == "triage"
    assert brief["input"] == "job7/traceback"
    assert any("llm_bad_shape" in line for line in brief["local_attempts"])
    # never the raw content re-dumped
    assert "spawn_actor" not in json.dumps(brief)
    from tee.kernel.budget import estimate_tokens

    assert estimate_tokens(json.dumps(brief)) <= router.BRIEF_TOKEN_CAP


def test_resident_engine_goes_first_when_state_says_q27b(tmp_path):
    (tmp_path / "llm-profile.json").write_text(json.dumps({"active": "q27b", "ready": True}))
    with fake_llm_server(_by_model({"fake-27b"})) as (url, calls):
        routed = _route(url, tmp_path)
    assert routed["ok"] and routed["engine"] == "q27b-bare"
    assert len(routed["hops"]) == 1  # the resident answered; no swap happened
    assert calls[0]["model"] == "fake-27b"


@pytest.mark.parametrize("mode", ["auto"])
def test_pin_lifecycle_via_the_switch_tool(tmp_path, mode):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.llm import profiles
    from tee.llm.tools import register_llm_tools

    project = tmp_path / "proj"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_llm_tools(app, project)
    out = app.registry.call("llm_switch", {"profile": "q27b"})
    assert out["ok"]
    assert profiles.load_state(app.llm_cfg).get("pinned") is True
    out = app.registry.call("llm_switch", {"profile": mode})
    assert "pin cleared" in out["report"]
    assert profiles.load_state(app.llm_cfg).get("pinned") is None
    app.shutdown()
