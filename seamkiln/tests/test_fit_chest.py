"""The fit report's chest: the trunk's widest slice below the armpit against
the cloth's own length round it.

The landmark rows compared a tape round the OUTSIDE of the garment (the
hull of its section) with a body girth at a fraction of stature, and the
body's "chest" came from the girth jump below the ribcage: a fitted tee
standing 20 mm off the body read 185 mm of ease for a pattern drafted with
44, and was called oversized. These pin the corrected row to the pattern.
"""

from __future__ import annotations

import pytest

from seamkiln.avatar import Pose
from seamkiln.drape.body import mannequin
from seamkiln.drape.measure import trunk_chest
from seamkiln.figure import chest_girth_m, figure
from seamkiln.session import Command, Session


def test_the_trunk_chest_is_the_torso_not_the_landmark_scan() -> None:
    """The mannequin's chest goes in as 1.00 m; its shoulder ledge is wider
    than its chest and must not be read as the chest."""
    body = mannequin()
    chest = trunk_chest(body)
    assert chest["girth_mm"] == pytest.approx(996.0, abs=6.0)
    assert 1.0 < chest["y_m"] < 1.3
    female = figure(Pose.a_pose(), height=1.65, build="female", chest_m=0.86)
    assert trunk_chest(female)["girth_mm"] == pytest.approx(
        chest_girth_m(female) * 1000.0, rel=0.025
    )


def test_the_chest_ease_is_the_pattern_ease_on_the_block() -> None:
    """The tee block's chest is 1,040 mm on a 996 mm mannequin: 44 mm of ease
    drafted, and the cloth's own loop reads it back to a few millimetres
    (measured 1,039.8, ease 43.9, "close") where the landmark row read 67."""
    s = Session()
    s.apply(Command("block", {"block": "tee"}))
    s.apply(Command("body", {"kind": "mannequin"}))
    s.apply(Command("arrange", {"particle_distance_mm": 12.0}))
    s.apply(Command("drape", {"fabric": "cotton_jersey", "frames": 280}))
    fit = s.apply(Command("fit", {}))
    chest = fit["chest"]
    assert chest["body_mm"] == pytest.approx(996.0, abs=6.0)
    assert chest["cloth_mm"] == pytest.approx(1040.0, rel=0.015)
    assert chest["ease_mm"] == pytest.approx(44.0, abs=16.0)
    assert chest["verdict"] == "close"
    assert chest["standing_mm"] >= chest["cloth_mm"] - 1.0
    assert "ease" in fit and "bust" in fit["ease"], "the landmark rows stay"


def test_a_garment_that_does_not_close_says_so() -> None:
    """Two panels hung round the body with no seam between them: no cloth
    loop closes, and the row says so instead of bridging the gap."""
    s = Session()
    s.apply(
        Command("panel", {"id": "FRONT", "outline": [[-200, 0], [200, 0], [200, 500], [-200, 500]]})
    )
    s.apply(
        Command("panel", {"id": "BACK", "outline": [[-200, 0], [200, 0], [200, 500], [-200, 500]]})
    )
    s.apply(Command("body", {"kind": "mannequin"}))
    s.apply(Command("arrange", {"particle_distance_mm": 20.0}))
    s.apply(Command("drape", {"fabric": "cotton_poplin", "frames": 40}))
    fit = s.apply(Command("fit", {"allow_unconverged": True}))
    chest = fit["chest"]
    assert chest["cloth_mm"] is None
    assert "do not close" in chest["note"]
