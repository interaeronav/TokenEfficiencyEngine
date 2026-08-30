"""A45 P0: the permission surface stops being a blockage - without the
taint law moving an inch. Each test is one of the owner's complaints."""

from __future__ import annotations

import time

import pytest

from tee.kernel import trust
from tee.kernel.errors import TeeError
from tee.kernel.registry import ToolRegistry, VirtualTool


def _cfg(**trust_section):
    class C:
        pass

    c = C()
    c.trust = dict(trust_section)
    return c


# -- P0a: a config edit is visible without a restart ------------------------


def test_grants_watcher_sees_an_edit_without_a_restart(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[trust]\n")
    state = {"grants": []}

    def loader():
        return trust.Grants.from_config(_cfg(grants=list(state["grants"])), source=str(path))

    w = trust.GrantsWatcher(path, loader)
    assert w().granted == frozenset()

    state["grants"] = ["exec-code"]
    time.sleep(0.01)
    path.write_text("[trust]\ngrants = ['exec-code']\n")  # bump mtime/size
    assert "exec-code" in w().granted, "an edit must land without a restart"


def test_watcher_does_not_restat_when_nothing_changed(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[trust]\n")
    calls = {"n": 0}

    def loader():
        calls["n"] += 1
        return trust.Grants.from_config(_cfg(), source=str(path))

    w = trust.GrantsWatcher(path, loader)
    for _ in range(5):
        w()
    assert calls["n"] == 1, "unchanged config must be read once, not per call"


def test_a_broken_config_fails_closed_rather_than_keeping_old_power(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[trust]\ngrants = ['exec-code']\n")
    state = {"boom": False}

    def loader():
        if state["boom"]:
            raise TeeError("bad", "unparseable", fix="fix the TOML")
        return trust.Grants.from_config(_cfg(grants=["exec-code"]), source=str(path))

    w = trust.GrantsWatcher(path, loader)
    assert "exec-code" in w().granted
    state["boom"] = True
    time.sleep(0.01)
    path.write_text("[trust]\ngrants = ['exec-code'\n")  # typo
    g = w()
    assert g.broken, "a typo must not silently retain the previous grants"
    d = trust.check("exec-code", caller="live-turn", grants=g)
    assert not d.allowed
    # ...but reads keep answering: a typo must never brick kb_search
    assert trust.check("read-kb", caller="live-turn", grants=g).allowed


def test_registry_reads_grants_through_the_watcher(tmp_path):
    reg = ToolRegistry()
    box = {"g": trust.Grants(granted=frozenset())}
    reg.grants_watcher = lambda: box["g"]
    assert reg.grants.granted == frozenset()
    box["g"] = trust.Grants(granted=frozenset({"exec-code"}))
    assert "exec-code" in reg.grants.granted
    # an explicit assignment still wins (tests and fakes rely on it)
    reg.grants = trust.Grants(granted=frozenset({"run-adhoc"}))
    assert reg.grants.granted == frozenset({"run-adhoc"})
    assert reg.grants_watcher is None


# -- P0b: one line grants a coherent set ------------------------------------


def test_profile_grants_a_named_set():
    g = trust.Grants.from_config(_cfg(profile="workstation"), source="x")
    assert {"exec-code", "run-adhoc", "run-declared-step"} <= g.granted
    assert g.profile == "workstation"


def test_profile_and_explicit_grants_compose():
    g = trust.Grants.from_config(_cfg(profile="build", grants=["exec-code"]), source="x")
    assert "run-declared-step" in g.granted  # from the profile
    assert "exec-code" in g.granted  # from the explicit list


def test_no_profile_smuggles_a_capability_it_does_not_name():
    # 'workstation' must not quietly include paid egress or policy writes
    assert "call-paid-engine" not in trust.PROFILES["workstation"]
    for name, caps in trust.PROFILES.items():
        assert "write-policy" not in caps, name
        assert "place-order" not in caps, name


def test_unknown_profile_refuses_loudly():
    with pytest.raises(TeeError) as e:
        trust.Grants.from_config(_cfg(profile="godmode"), source="x")
    assert "not a known profile" in e.value.message


# -- P0d: the refusal carries the fix ---------------------------------------


def test_refusal_names_the_file_the_line_and_the_profile():
    g = trust.Grants(granted=frozenset(), source="/Users/x/.tee/config.toml")
    d = trust.check("exec-code", caller="live-turn", grants=g)
    fix = d.fix()
    assert "/Users/x/.tee/config.toml" in fix
    assert 'grants = ["exec-code"]' in fix
    assert "workstation" in fix, "offer the one-line profile too"
    assert "no restart" in fix


# -- the law that does NOT move ---------------------------------------------


def test_taint_still_blocks_every_automated_caller_even_when_granted():
    g = trust.Grants.from_config(_cfg(profile="workstation+paid"), source="x")
    for caller in ("chore", "job", "scheduled", "gateway-fronted", "content-derived"):
        for cap in ("exec-code", "run-adhoc", "call-paid-engine", "run-declared-step"):
            d = trust.check(cap, caller=caller, grants=g, taint=("fetch-web:x",))
            assert not d.allowed, f"{caller}/{cap} must refuse while tainted"
            assert d.enforced, f"{caller}/{cap} must enforce now, not in shadow"


def test_a_live_turn_still_needs_consent_for_high_risk_while_tainted():
    g = trust.Grants.from_config(_cfg(profile="workstation"), source="x")
    assert not trust.check(
        "exec-code", caller="live-turn", grants=g, taint=("fetch-web:x",)
    ).allowed
    assert trust.check(
        "exec-code", caller="live-turn", grants=g, taint=("fetch-web:x",), consent=True
    ).allowed


def test_place_order_is_reserved_and_no_tool_requests_it():
    assert "place-order" in trust.CAPABILITIES
    assert "place-order" in trust.HIGH_RISK
    tabled = set(trust._EXPLICIT.values()) | {c for _, c in trust._FAMILY}
    assert "place-order" not in tabled, "no tool may request place-order"


def test_new_fleet_families_are_tabled():
    """NOTE trade_ and cad_ are deliberately absent as FAMILIES: a trading
    tool must never inherit a capability by name, and a cad tool that
    builds writes a file while one that measures does not. Both are tabled
    individually in _EXPLICIT."""
    for name, expect in (
        ("solve_milp", "read-compute"),
        ("quant_efficient_frontier", "read-compute"),
        ("med_dicom_series", "read-medimg"),
        ("bi_query", "call-service"),
    ):
        assert trust.capability_for(name) == expect


def test_an_untabled_tool_still_refuses_to_ship():
    with pytest.raises(TeeError):
        trust.capability_for("wat_no_family_here")


def test_read_compute_is_open_by_default():
    g = trust.Grants()  # a brand new project, nothing granted
    assert trust.check("read-compute", caller="chore", grants=g).allowed
    assert trust.check("read-medimg", caller="job", grants=g).allowed
    # ...but a service call is not
    assert not trust.check("call-service", caller="chore", grants=g).allowed


def test_registering_a_fleet_tool_needs_no_kernel_edit():
    reg = ToolRegistry()
    reg.register(
        VirtualTool(
            name="solve_lp",
            description="s",
            schema={"type": "object", "properties": {}},
            handler=lambda a: {},
        )
    )
    assert reg._tools["solve_lp"].capability == "read-compute"


# -- A45 P2: two holes the adversarial trading-safety analysis found -------
#
# Both were live in code shipped earlier the same night, and both were the
# same class of mistake: a guard that depended on nobody adding a thing,
# rather than on the thing being impossible.


def test_no_family_prefix_covers_a_trading_tool():
    """A ('trade_', 'read-compute') prefix existed. It would have let a tool
    called trade_place_order inherit the OPEN read tier purely by being
    named - no review, no grant, no startup error. Trading tools must be
    tabled INDIVIDUALLY so an untabled one cannot boot."""
    assert not any(p == "trade_" for p, _ in trust._FAMILY)
    with pytest.raises(TeeError) as e:
        trust.capability_for("trade_place_order")
    assert e.value.code == "trust_untabled_tool"


def test_place_order_can_never_be_granted_by_a_config_line():
    """It sat in CAPABILITIES, so `grants = ["place-order"]` parsed happily.
    Combined with A45 P0a's hot reload, one edited line would have activated
    it with no restart and no prompt. The line must now fail to parse."""
    with pytest.raises(TeeError) as e:
        trust.Grants.from_config(_cfg(grants=["place-order"]), source="x")
    assert e.value.code == "trust_never_grantable"
    assert "broker" in e.value.fix


def test_no_profile_can_smuggle_a_never_grantable_capability():
    for name, caps in trust.PROFILES.items():
        assert not (caps & trust.NEVER_GRANTABLE), name


def test_never_grantable_survives_the_hot_reload_path(tmp_path):
    """The reload is the attack surface P0a created; assert it too."""
    path = tmp_path / "config.toml"
    path.write_text("[trust]\n")
    state = {"grants": []}

    def loader():
        return trust.Grants.from_config(_cfg(grants=list(state["grants"])), source=str(path))

    w = trust.GrantsWatcher(path, loader)
    assert w().granted == frozenset()
    state["grants"] = ["place-order"]
    time.sleep(0.01)
    path.write_text("[trust]\ngrants = ['place-order']\n")
    g = w()
    assert g.broken, "an ungrantable line must break the config, not activate"
    assert "place-order" not in g.granted
    assert not trust.check("place-order", caller="live-turn", grants=g, consent=True).allowed
