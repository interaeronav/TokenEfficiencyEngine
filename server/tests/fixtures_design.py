"""Design fixtures: a balanced small-team 3D co-op spec (the skill-eval
brief) and seeded-defect variants."""

from __future__ import annotations

import copy
from typing import Any


def coop_spec() -> dict[str, Any]:
    """A scoped 3D co-op brief that should pass every checker and sit on
    the evidence-backed opportunity map (research 29)."""
    return {
        "spec": "tee-design/1",
        "name": "Salvage Crew",
        "meta": {
            "platform": "pc",
            "price_usd": 15,
            "min_age": 13,
            "team_size": 4,
            "audience": {
                "motivations": {
                    "community": 0.9, "excitement": 0.7, "discovery": 0.6,
                    "competition": 0.2, "completion": 0.4,
                },
                "age_range": [16, 34],
            },
            "comparables": [
                {"name": "R.E.P.O.", "delta": "underwater physics + air as the shared timer"},
                {"name": "Lethal Company",
                 "delta": "no quota death-spiral; wholesale co-op economy"},
                {"name": "Peak", "delta": "salvage crane co-op instead of climbing"},
            ],
        },
        "core_loop": {
            "verbs": ["dive", "salvage", "haul", "upgrade"],
            "steps": [
                {"action": "plan the dive", "target_s": 60},
                {"action": "dive and salvage", "target_s": 480},
                {"action": "haul and sell", "target_s": 120},
                {"action": "upgrade the rig", "target_s": 90},
            ],
            "failure_state": "air runs out - crew surfaces, hold cargo kept, held items lost",
            "session_end_hook": "tomorrow's wreck chart is revealed at sell-time",
        },
        "economy": {
            "archetype": "premium_session",
            "currencies": ["scrap", "credits"],
            "nodes": [
                {"kind": "faucet", "currency": "scrap", "rate": 60},
                {"kind": "converter", "from": "scrap", "to": "credits", "rate": 55, "ratio": 1.0},
                {"kind": "sink", "currency": "credits", "rate": 50},
                {"kind": "sink", "currency": "scrap", "rate": 6},
            ],
        },
        "progression": {
            "unlocks": [
                {"id": "u_winch", "at": 1, "teaches": "winch", "difficulty": 1},
                {"id": "u_cutter", "at": 2, "teaches": "cutter", "difficulty": 2,
                 "requires": ["u_winch"]},
                {"id": "u_sonar", "at": 3, "teaches": "sonar", "difficulty": 3,
                 "requires": ["u_cutter"]},
                {"id": "u_deep", "at": 6, "difficulty": 4, "requires": ["u_sonar"]},
            ],
        },
        "level_macro": {
            "beats": [
                {"space": "shallows", "mechanics": ["winch"], "intensity": 1,
                 "content_classes": ["environment_set"]},
                {"space": "reef wreck", "mechanics": ["winch", "cutter"], "intensity": 3,
                 "exotics": ["moray den"], "content_classes": ["environment_set", "prop"]},
                {"space": "trench", "mechanics": ["cutter", "sonar"], "intensity": 5,
                 "content_classes": ["environment_set", "creature"]},
                {"space": "the liner", "mechanics": ["winch", "cutter", "sonar"], "intensity": 7,
                 "exotics": ["collapsing deck"], "content_classes": ["level"]},
            ],
        },
        "content_list": [
            {"class": "environment_set", "count": 4},
            {"class": "prop", "count": 40, "reuse": 0.5},
            {"class": "creature", "count": 3},
            {"class": "character", "count": 2, "reuse": 0.5},
            {"class": "level", "count": 4},
            {"class": "mechanic_system", "count": 4},
            {"class": "sfx", "count": 60, "reuse": 0.3},
            {"class": "music", "count": 4},
            {"class": "ui_screen", "count": 6},
        ],
        "routine": {
            "daily": "wreck chart rotation",
            "weekly": "tide event (Tuesday 17:00 UTC)",
            "streak": {"grace_days": 2},
        },
        "accessibility": {
            "subtitles_default_on": True,
            "remapping": True,
            "color_only_information": False,
        },
        "monetization": {"model": "premium", "loot_boxes": False},
        "open_questions": ["proximity voice: built-in or platform-native?"],
    }


def with_defects(**kinds) -> dict[str, Any]:
    """Seed named defects into a copy of the balanced spec."""
    spec = copy.deepcopy(coop_spec())
    if kinds.get("dead_currency"):
        spec["economy"]["currencies"].append("gems")
        spec["economy"]["nodes"].append({"kind": "faucet", "currency": "gems", "rate": 5})
    if kinds.get("no_hook"):
        del spec["core_loop"]["session_end_hook"]
    if kinds.get("taught_after_use"):
        # sonar used in beat 3 but its unlock moved to position 9
        for unlock in spec["progression"]["unlocks"]:
            if unlock["id"] == "u_sonar":
                unlock["at"] = 9
    if kinds.get("inflation"):
        spec["economy"]["nodes"] = [
            {"kind": "faucet", "currency": "scrap", "rate": 100},
            {"kind": "faucet", "currency": "scrap", "rate": 40},
            {"kind": "sink", "currency": "scrap", "rate": 5},
            {"kind": "faucet", "currency": "credits", "rate": 10},
            {"kind": "sink", "currency": "credits", "rate": 10},
        ]
    if kinds.get("minor_lootbox"):
        spec["meta"]["min_age"] = 12
        spec["monetization"] = {
            "model": "f2p",
            "loot_boxes": True,
            "odds_disclosed": False,
            "virtual_currency": True,
            "currency_hops": 2,
        }
    return spec
