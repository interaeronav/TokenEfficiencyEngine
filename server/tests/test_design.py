"""Phase 10: tee-design/1 spec, reference tables, verification battery."""

from __future__ import annotations

import pytest
from fixtures_design import coop_spec, with_defects

from tee.design import checks, tables
from tee.design.spec import SpecStore, render_one_pager, validate
from tee.kernel.errors import TeeError

# -- spec validation + round-trip ------------------------------------------


def test_validate_balanced_spec():
    out = validate(coop_spec())
    assert out["ok"] and "core_loop" in out["sections"]


def test_validate_names_exact_fix():
    spec = coop_spec()
    spec["economy"]["nodes"].append({"kind": "sink", "currency": "gold", "rate": 1})
    with pytest.raises(TeeError) as err:
        validate(spec)
    assert "gold" in err.value.message
    assert "economy.currencies" in (err.value.fix or "")

    bad = coop_spec()
    bad["meta"]["audience"]["motivations"]["swagger"] = 0.5
    with pytest.raises(TeeError) as err:
        validate(bad)
    assert "swagger" in err.value.message


def test_spec_roundtrip_store_edit_revalidate(tmp_path):
    """Acceptance: validate -> render -> edit -> re-validate round trip."""
    store = SpecStore(tmp_path)
    first = store.save(coop_spec())
    assert first["revision"] == 1
    prose = render_one_pager(store.load("salvage_crew"))
    assert "Salvage Crew" in prose and "R.E.P.O." in prose
    edited = store.load("salvage_crew")
    edited["core_loop"]["verbs"].append("photograph")
    second = store.save(edited)
    assert second["revision"] == 2
    assert second["changed_sections"] == ["core_loop"]
    assert validate(store.load("salvage_crew"))["ok"]


# -- reference tables ------------------------------------------------------


def test_benchmark_answers_with_source_never_folk():
    """Acceptance: 'what is a good D7 for mobile puzzle' -> grid + source +
    year, never a folk target."""
    out = tables.benchmark("d7", platform="mobile", genre="puzzle")
    assert out["grid"]["median"] == 0.04
    assert "GameAnalytics 2026" in out["grid"]["source"]
    assert "top DECILE" in out["note"]  # the folk-target warning travels
    assert out["genre_d30"]["value"] == 0.054
    assert "AppsFlyer" in out["genre_d30"]["source"]


def test_benchmark_unknown_metric_names_fix():
    with pytest.raises(TeeError) as err:
        tables.benchmark("nps")
    assert "d1, d7, d30" in (err.value.fix or "")


def test_genre_conventions_and_opportunity():
    coop = tables.genre_conventions("coop_3d")
    assert coop["price_band_usd"] == [8, 25]
    avoid = tables.genre_conventions("platformer")
    assert avoid.get("avoid") is True
    top = tables.opportunity_map()[0]
    assert top["rank"] == 1 and "co-op" in top["what"]


# -- lint -------------------------------------------------------------------


def test_lint_clean_on_balanced_spec():
    assert checks.lint(coop_spec())["findings"] == []


def test_lint_dead_currency():
    findings = checks.lint(with_defects(dead_currency=True))["findings"]
    dead = [f for f in findings if f["code"] == "dead_currency"]
    assert dead and "gems" in dead[0]["message"] and "sink" in dead[0]["fix"]


def test_lint_missing_session_end_hook():
    findings = checks.lint(with_defects(no_hook=True))["findings"]
    assert any(f["code"] == "no_session_end_hook" for f in findings)


def test_lint_taught_after_use():
    findings = checks.lint(with_defects(taught_after_use=True))["findings"]
    hits = [f for f in findings if f["code"] == "used_before_taught"]
    assert hits and "sonar" in hits[0]["message"]


def test_lint_differentiation_forcing():
    spec = coop_spec()
    spec["meta"]["comparables"] = spec["meta"]["comparables"][:1]
    findings = checks.lint(spec)["findings"]
    assert any(f["code"] == "underdifferentiated" for f in findings)


def test_lint_audience_contradiction():
    spec = coop_spec()
    spec["meta"]["audience"]["motivations"]["competition"] = 0.9
    spec["meta"]["audience"]["age_range"] = [35, 55]
    findings = checks.lint(spec)["findings"]
    hit = [f for f in findings if f["code"] == "audience_contradiction"]
    assert hit and "age" in hit[0]["message"]


# -- economy sim ------------------------------------------------------------


def test_economy_sim_passes_balanced():
    out = checks.economy_sim(coop_spec())
    assert out["flags"] == []
    ratios = out["currencies"]["scrap"]["sink_faucet_ratio"]
    assert all(r and 0.6 <= r <= 1.1 for r in ratios.values())


def test_economy_sim_flags_inflation():
    """Acceptance: a seeded inflation spiral is flagged."""
    out = checks.economy_sim(with_defects(inflation=True))
    codes = {f["code"] for f in out["flags"]}
    assert "archetype_band" in codes or "inflation" in codes
    flagged = out["flags"][0]
    assert "sink" in flagged["fix"]


# -- progression ------------------------------------------------------------


def test_progression_clean_and_spike():
    assert checks.progression_check(coop_spec())["findings"] == []
    spec = coop_spec()
    spec["progression"]["unlocks"].append({"id": "u_wall", "at": 7, "difficulty": 9})
    findings = checks.progression_check(spec)["findings"]
    assert any(f["code"] == "difficulty_spike" for f in findings)


def test_pity_hazard_math():
    spec = coop_spec()
    spec["progression"]["pity"] = {
        "base": 0.006,
        "soft_start": 74,
        "increment": 0.06,
        "hard": 90,
        "disclosed": True,
        "expected_pulls": 62.5,
    }
    findings = checks.progression_check(spec)["findings"]
    assert findings == []  # Genshin's published params are self-consistent
    spec["progression"]["pity"]["expected_pulls"] = 20
    findings = checks.progression_check(spec)["findings"]
    assert any(f["code"] == "pity_math" for f in findings)


# -- ethics -----------------------------------------------------------------


def test_ethics_hard_fails_minor_lootbox():
    """Acceptance: under-16 loot-box spec hard-fails citing rule +
    jurisdiction."""
    out = checks.ethics_check(with_defects(minor_lootbox=True))
    assert out["hard_fail"] is True
    codes = {v["code"] for v in out["violations"]}
    assert {"loot_box_minors", "odds_disclosure", "multi_hop_currency"} <= codes
    minors = next(v for v in out["violations"] if v["code"] == "loot_box_minors")
    assert any("Belgium" in j for j in minors["jurisdictions"])
    assert minors["severity"] == "code"


def test_ethics_clean_on_premium():
    out = checks.ethics_check(coop_spec())
    assert out["hard_fail"] is False and out["violations"] == []


def test_ethics_streak_grace_rule():
    spec = coop_spec()
    spec["routine"]["streak"] = {"grace_days": 0}
    out = checks.ethics_check(spec)
    assert any(v["code"] == "streak_no_grace" for v in out["violations"])


# -- self-play ---------------------------------------------------------------


def test_selfplay_prepare_and_score():
    spec = coop_spec()
    prep = checks.selfplay_prepare(spec, turns=6)
    assert "dive" in prep["verbs"] and "6 turns" in prep["instructions"]
    good = [
        {"turn": i, "verb": v, "decision": i % 2 == 0}
        for i, v in enumerate(["dive", "salvage", "haul", "upgrade", "dive", "salvage"], 1)
    ]
    score = checks.selfplay_score(spec, good)
    assert score["findings"] == [] and len(score["distinct_verbs"]) == 4
    boring = [{"turn": i, "verb": "dive", "decision": False} for i in range(1, 7)]
    score = checks.selfplay_score(spec, boring)
    codes = {f["code"] for f in score["findings"]}
    assert {"no_decision_loop", "forced_moves"} <= codes


# -- the battery + skill-eval acceptance ------------------------------------


def test_battery_on_balanced_coop_brief():
    """Acceptance: the small-team 3D co-op brief names 3 comparables,
    passes all checkers, and its content_list resolves against Phase 9
    asset classes."""
    from tee.assets.envelopes import load_envelopes  # Phase 9 alive
    from tee.design.spec import ASSET_CLASSES

    spec = coop_spec()
    out = checks.run_battery(spec)
    assert out["verdict"] == "all checkers pass", out
    assert out["hard_fail"] is False
    assert len(spec["meta"]["comparables"]) == 3
    for entry in spec["content_list"]:
        assert entry["class"] in ASSET_CLASSES
    assert load_envelopes()  # the Phase 9 side of the bridge exists


def test_battery_hard_fail_verdict():
    out = checks.run_battery(with_defects(minor_lootbox=True))
    assert out["hard_fail"] is True and "HARD FAIL" in out["verdict"]


def test_scope_estimate_flags_capacity():
    spec = coop_spec()
    out = checks.scope_estimate(spec, team_size=4, weeks=40)
    assert out["person_days"][0] > 0 and "flag" not in out
    tight = checks.scope_estimate(spec, team_size=1, weeks=4)
    assert "flag" in tight and "capacity" in tight["flag"]


# -- tools registration ------------------------------------------------------


def test_gd_tools_end_to_end(tmp_path):
    from tee.app import TeeApp
    from tee.design.tools import register_design_tools
    from tee.kernel.adapter import FakeAdapter

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_design_tools(app, tmp_path)
    for name in (
        "gd_validate",
        "gd_store",
        "gd_check",
        "gd_benchmark",
        "gd_genre",
        "gd_ethics",
        "gd_selfplay",
        "gd_render",
    ):
        assert name in app.registry.names()
    app.registry.call("gd_store", {"spec": coop_spec()})
    out = app.registry.call("gd_check", {"name": "salvage_crew"})
    assert out["verdict"] == "all checkers pass"
    rendered = app.registry.call("gd_render", {"name": "salvage_crew", "view": "beat_chart"})
    assert "trench" in rendered["markdown"]
    bench = app.registry.call("gd_benchmark", {"metric": "d7", "platform": "mobile"})
    assert "source" in bench["grid"]
