"""The body lane (A53 P3): Anny, landmarks, measurements, ease and fit.

Anny is an optional extra, so every test that needs it skips cleanly. What
does NOT skip is the licence guard: the one door Anny leaves open to a
non-commercial dependency is closed here whether Anny is installed or not.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.drape.anny_body import BANNED_TOPOLOGY, load_topology
from seamkiln.drape.body import body_shell, mannequin, sdf_from_mesh
from seamkiln.drape.garment import arm_axes, body_landmarks, build_garment, top_arrangement
from seamkiln.drape.measure import (
    LANDMARKS,
    body_measurements,
    ease,
    fit_report,
    strain_map,
    torso_panels,
)
from seamkiln.drape.solve import DrapeSettings, drape
from seamkiln.pattern.fixtures import tee_block

# -- the licence guard (runs with or without Anny installed) -----------------


def test_the_non_commercial_topology_is_refused_by_name() -> None:
    """Anny is Apache-2.0, but its optional smplx topology is downloadable
    for NON-COMMERCIAL use only. Apache-2.0 on the tin does not make every
    door inside it open."""
    with pytest.raises(ValueError, match="NON-COMMERCIAL"):
        load_topology("smplx")
    assert "smplx" in BANNED_TOPOLOGY
    assert load_topology("anny") == "anny"
    assert load_topology("soma") == "soma"
    with pytest.raises(ValueError, match="unknown Anny topology"):
        load_topology("smpl-h")


# -- shells ------------------------------------------------------------------


def test_small_inner_shells_are_dropped_and_limbs_are_not() -> None:
    """Anny ships eyeballs and a tongue as separate closed shells inside the
    head; they made landmark detection fire at eye height. Keeping only the
    LARGEST shell was the first fix and it threw away the mannequin's arms,
    head and legs - it is assembled from overlapping capsules that never
    share vertices."""
    body = mannequin()
    assert len(body_shell(body).faces) == len(body.faces), "a limb was discarded"

    import trimesh

    speck = trimesh.creation.icosphere(subdivisions=1, radius=0.01)
    speck.apply_translation([0.0, 1.5, 0.0])
    with_speck = trimesh.util.concatenate([body, speck])
    assert len(body_shell(with_speck).faces) < len(with_speck.faces)


# -- landmarks on the stand-in body ------------------------------------------


def test_landmarks_are_ordered_the_way_a_body_is() -> None:
    marks = body_landmarks(mannequin())
    assert marks["neck_y_m"] > marks["shoulder_y_m"] > marks["armpit_y_m"]
    assert marks["chest_girth_m"] > marks["neck_girth_m"]


def test_arms_are_never_measured_from_a_foot() -> None:
    """The first measured version read the arm from the innermost outboard
    vertex to the outermost, which on a real body means from a FOOT to a
    hand: shoulder at y = 0.015 m and an arm pointing upward."""
    body = mannequin()
    marks = body_landmarks(body)
    for side, arm in arm_axes(body, marks["chest_radius_m"]).items():
        assert float(arm["shoulder"][1]) > marks["armpit_y_m"], f"{side} shoulder is too low"
        assert float(arm["direction"][1]) < 0.0, f"{side} arm points upward"
        assert 0.02 < float(arm["radius_m"]) < 0.12, f"{side} arm radius is not an arm"


def test_measurements_read_like_a_tape_measure() -> None:
    rows = body_measurements(mannequin())
    assert rows["chest_girth_mm"] == pytest.approx(1000.0, rel=0.03)
    assert set(rows["landmarks"]) <= set(LANDMARKS)
    for row in rows["landmarks"].values():
        assert row["girth_mm"] > 0.0


# -- ease and strain ---------------------------------------------------------


def test_ease_is_reported_per_landmark_with_a_verdict() -> None:
    body_rows = {"landmarks": {"bust": {"girth_mm": 900.0}, "waist": {"girth_mm": 800.0}}}
    garment_rows = {"bust": {"girth_mm": 1000.0}, "waist": {"girth_mm": 790.0}}
    result = ease(garment_rows, body_rows)
    assert result["bust"]["ease_mm"] == pytest.approx(100.0)
    assert result["bust"]["verdict"] == "relaxed"
    assert result["waist"]["ease_mm"] == pytest.approx(-10.0)
    assert "will not close" in result["waist"]["verdict"]


def test_sleeves_do_not_inflate_a_bust_measurement() -> None:
    """Hulling every panel at bust height spans BOTH SLEEVES and reported
    1,374 mm on an 890 mm body - a normal tee called oversized by half a
    metre. A torso panel straddles the centre line; a sleeve does not."""
    body = mannequin()
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=25.0)
    assert set(torso_panels(garment, garment.points)) == {"FRONT", "BACK"}


def test_strain_excludes_sliver_edges_and_says_how_many() -> None:
    """A 0.1 mm rest edge stretched 3 mm is 3,000% strain and says nothing
    about the fabric, but it does drown out every real number."""
    body = mannequin()
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=25.0)
    report = strain_map(garment, garment.points)
    assert "sliver_edges_excluded" in report
    assert report["overall_p99_pct"] <= report["overall_max_pct"]
    assert set(report["panels"]) == set(garment.panel_slices)


# -- Anny itself (skips when the extra is absent) ----------------------------


@pytest.fixture(scope="module")
def anny():
    pytest.importorskip("anny", reason="seamkiln[body] not installed")
    from seamkiln.drape.anny_body import anny_body

    return anny_body(stature_m=1.75)


def test_anny_arrives_in_seamkilns_world(anny) -> None:
    """Metres, Y up, feet on the floor. Anny's own world is Z-up."""
    from seamkiln.drape.anny_body import describe

    low, high = anny.bounds
    assert float(low[1]) == pytest.approx(0.0, abs=1e-6), "the body is not standing on y = 0"
    assert float(high[1] - low[1]) == pytest.approx(1.75, abs=1e-3)
    assert float(high[1] - low[1]) > float(high[0] - low[0]), (
        "a person is taller than they are wide"
    )
    assert describe(anny)["watertight"] is True


def test_anny_measures_like_a_person(anny) -> None:
    marks = body_landmarks(anny)
    height = marks["height_m"]
    assert 0.78 < marks["shoulder_y_m"] / height < 0.88
    assert marks["armpit_y_m"] < marks["shoulder_y_m"]
    assert 0.30 < marks["neck_girth_m"] < 0.45  # a neck, in metres
    assert 0.70 < marks["chest_girth_m"] < 1.20  # a chest, in metres


def test_a_real_body_wears_the_tee(anny) -> None:
    """The end-to-end case: pattern -> mesh -> arrange -> drape -> fit."""
    pattern = tee_block()
    sdf = sdf_from_mesh(anny, voxel_mm=10.0)
    garment = build_garment(pattern, top_arrangement(pattern, anny), particle_distance=20.0)
    result = drape(garment, sdf, fabric="cotton_jersey", settings=DrapeSettings(frames=200))

    assert result.contact["worn"] is True
    assert result.penetration["deepest_penetration_mm"] < 25.0
    assert result.seam_gaps["mean_gap_mm"] < 5.0
    assert np.isfinite(result.points).all()

    report = fit_report(garment, result.points, anny)
    assert report["ease"], "no landmark could be compared"
    for row in report["ease"].values():
        assert row["garment_mm"] > row["body_mm"], "a tee should not be smaller than the body"
