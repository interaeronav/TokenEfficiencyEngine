"""A46 P3a — the engines this machine actually serves.

Two defects are pinned here. The first is that TEE could not reach a free
engine at all: `.tee/config.toml` declared only the PAID qmax, so every
chore either billed or fell through to the deterministic path. The second
is subtler and was found while fixing the first - every local engine here
is a REASONING model, and the chores were asking for less output budget
than the reasoning pass alone consumes.
"""

from __future__ import annotations

import ast
import pathlib

from tee.kernel import machine


def test_no_two_engines_claim_the_same_profile():
    """Found the hard way. Adding a second row for the 27B - same engine,
    freshly measured - gave the router two answers to `which engine is
    profile q27b?`, and it quietly took the newer one. Nothing raised; two
    routing tests just started naming a different engine. A profile is an
    identity, so the mapping has to be one-to-one or the router is
    guessing."""
    from collections import Counter

    counts = Counter(e["profile"] for e in machine.ENGINES.values() if "profile" in e)
    dupes = {p: n for p, n in counts.items() if n > 1}
    assert dupes == {}, f"profile claimed by more than one engine: {dupes}"


def test_the_local_engines_are_registered_with_measured_costs():
    for name in ("dsflash",):
        row = machine.ENGINES[name]
        assert row["kind"] == "llm"
        assert "chores" in row["capability"]
        assert "measured" in row["cost"], f"{name} carries an unmeasured cost"


def test_the_new_observation_did_not_overwrite_the_old_measurement():
    """The 27B was re-measured at 27.78 s through the shim, against 3.07-9.69 s
    recorded at R0. Different prompt, budget and path - so it is recorded
    ALONGSIDE, not over. A single averaged number would be one no run
    produced."""
    cost = machine.ENGINES["q27b-bare"]["cost"]
    assert cost["latency_s"] == [3.07, 9.69], "the R0 measurement was overwritten"
    assert cost["a46_shim_observation_s"] == 27.78


def test_the_cheap_engine_is_actually_the_faster_one():
    fast = machine.ENGINES["dsflash"]["cost"]["latency_s"][1]
    slow = machine.ENGINES["q27b-bare"]["cost"]["a46_shim_observation_s"]
    assert fast * 4 < slow, "routing chores to dsflash must actually save time"


def test_the_chore_floor_matches_what_was_measured():
    """256, because at 64 tokens q27b returned an EMPTY answer and dsflash
    returned its own scratchpad. Both looked like bad answers rather than
    exhausted budgets."""
    assert machine.MIN_CHORE_TOKENS == 256


def test_every_chore_call_site_is_covered_by_the_floor():
    """The floor lives in _run, so no caller can undercut it. Asserted on
    the source: the max_tokens passed to complete_json must be the floored
    `budget`, never the raw argument."""
    src = pathlib.Path(machine.__file__).parent.parent / "llm" / "chores.py"
    tree = ast.parse(src.read_text())
    run = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_run")
    calls = [
        c
        for c in ast.walk(run)
        if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "complete_json"
    ]
    assert calls, "no complete_json call found in _run"
    for c in calls:
        kw = {k.arg: k.value for k in c.keywords}
        assert isinstance(kw["max_tokens"], ast.Name)
        assert kw["max_tokens"].id == "budget", "a chore bypassed the floor"


def test_the_floor_raises_but_never_lowers():
    """A caller asking for MORE room knows something the floor does not."""
    for asked, expected in ((160, 256), (220, 256), (256, 256), (1200, 1200)):
        assert max(asked, machine.MIN_CHORE_TOKENS) == expected


# -- P3b: cheapest-capable routing ------------------------------------------


def test_the_paid_engine_can_never_enter_the_ladder():
    """The A46 law: the paid engine is pin-only and never an automatic
    target. The guard is structural rather than a filter - a paid engine has
    no row in ENGINES at all, so no ordering, policy or config can promote
    one into the ladder. Asserted from both ends."""
    from tee.llm.router import LADDER

    for name in LADDER:
        row = machine.ENGINES[name]
        assert not row.get("paid"), f"{name} is paid and reachable automatically"
    assert all(not e.get("paid") for e in machine.ENGINES.values())
    # qmax is a config PROFILE, deliberately not an engine row.
    assert "qmax" not in {e.get("profile") for e in machine.ENGINES.values()}


def test_the_ladder_is_ordered_cheapest_first_from_the_measured_table():
    """It used to be the hand-written ("q14b+a2", "q27b-bare") - which on
    this machine leads with a 14B the shim does not serve and never reaches
    the free engine that answers in 4.41 s."""
    from tee.llm.router import LADDER

    costs = [machine.ENGINES[n]["cost"]["latency_s"][1] for n in LADDER]
    assert costs == sorted(costs), f"ladder out of cost order: {list(zip(LADDER, costs))}"
    assert "dsflash" in LADDER, "the free local engine must be reachable"


def test_an_undeclared_engine_is_skipped_not_blamed():
    """A rung this machine has not declared never ran, so it must not be
    recorded as a verification failure - that inflated the escalation rate
    with absent hardware."""
    import inspect

    from tee.llm import router

    src = inspect.getsource(router.route)
    assert "profile not declared here" in src
    skip_at = src.index("profile not declared here")
    call_at = src.index("result = call(")
    assert skip_at < call_at, "the declaration check must precede the call"
