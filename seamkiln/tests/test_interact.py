"""Pulling cloth around by hand, and whether it answers fast enough to matter.

The gestures are easy; the clock is the point. These tests assert the measured
rate as well as the behaviour, because "interactive adjustment" that takes a
second a frame is not interactive adjustment.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.drape.body import mannequin, sdf_from_mesh
from seamkiln.drape.garment import build_garment, top_arrangement
from seamkiln.drape.solve import DrapeSettings, drape, prepare
from seamkiln.interact import LiveSession
from seamkiln.pattern.fixtures import tee_block


@pytest.fixture(scope="module")
def draped():
    body = mannequin()
    field = sdf_from_mesh(body, voxel_mm=6.0)
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=16.0)
    garment.points = drape(
        garment, field, fabric="cotton_poplin", settings=DrapeSettings(frames=200)
    ).points.copy()
    return garment, field, garment.points.copy()


def _fresh(draped):
    garment, field, rest = draped
    garment.points = rest.copy()
    return garment, field


# -- the cache that makes it possible ------------------------------------------


def test_a_prepared_solve_is_a_cache_and_not_an_approximation(draped) -> None:
    """Bit-identical, or it is not a cache. Same fingerprint, zero position
    difference - which is what lets the interactive path use it without the
    interactive answer differing from the batch one."""
    garment, field = _fresh(draped)
    rest = garment.points.copy()
    options = DrapeSettings(frames=3, substeps=12)
    prepared = prepare(garment, fabric="cotton_poplin", settings=options)

    garment.points = rest.copy()
    rebuilt = drape(garment, field, fabric="cotton_poplin", settings=options)
    garment.points = rest.copy()
    cached = drape(garment, field, fabric="cotton_poplin", settings=options, prepared=prepared)

    assert rebuilt.fingerprint == cached.fingerprint
    assert float(np.abs(rebuilt.points - cached.points).max()) == 0.0


def test_a_stale_graph_is_refused_rather_than_used(draped) -> None:
    """The prepared arrays ARE the constraint graph, so anything that changes
    the graph has to invalidate them. Silently solving against a stale one
    would be wrong in a way nothing downstream could detect."""
    garment, field = _fresh(draped)
    options = DrapeSettings(frames=1, substeps=12)
    prepared = prepare(garment, fabric="cotton_poplin", settings=options)

    with pytest.raises(ValueError, match="does not match this garment"):
        drape(garment, field, fabric="denim_12oz", settings=options, prepared=prepared)

    body = mannequin()
    other = build_garment(tee_block(), top_arrangement(tee_block(), body), particle_distance=22.0)
    with pytest.raises(ValueError, match="re-mesh"):
        drape(other, field, fabric="cotton_poplin", settings=options, prepared=prepared)


def test_the_key_is_the_rooms_content_not_its_identity() -> None:
    """`DrapeSettings.room` builds a fresh Environment on every access when
    none was set, so keying on its identity meant a prepared solve could never
    match anything - including the settings object it was built from."""
    from seamkiln.drape.solve import _prepare_key
    from seamkiln.pattern.fabric import fabric as fabric_by_name

    body = mannequin()
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=22.0)
    options = DrapeSettings(frames=1)
    cloth = fabric_by_name("cotton_poplin")
    assert options.room is not options.room  # a fresh object every access
    assert _prepare_key(garment, cloth, options) == _prepare_key(garment, cloth, options)


# -- the gestures --------------------------------------------------------------


def test_a_drag_runs_at_an_interactive_rate_and_says_what_it_achieved(draped) -> None:
    """Measured, never claimed: about 43 fps on a 4,549-particle t-shirt, from
    18 fps before the constraint graph was cached."""
    garment, field = _fresh(draped)
    live = LiveSession(garment, field, fabric="cotton_poplin")
    hem = garment.points[int(np.argmin(garment.points[:, 1]))]
    handle = live.grab(tuple(hem), radius_mm=50.0)
    for k in range(1, 13):
        live.drag(handle, (hem[0] + 0.004 * k, hem[1] + 0.002 * k, hem[2] - 0.005 * k))
    rate = live.rate()
    assert rate["steps"] == 12
    assert rate["interactive"] is True
    assert rate["ms_per_step"] < 60.0, rate
    assert handle.travel_mm > 50.0


def test_a_settle_is_reported_separately_from_a_drag(draped) -> None:
    """Averaging them together is a lie in both directions: one 40-frame
    settle took the reported rate of a 43 fps drag down to 2.2 fps, which
    describes neither thing that happened."""
    garment, field = _fresh(draped)
    live = LiveSession(garment, field, fabric="cotton_poplin")
    hem = garment.points[int(np.argmin(garment.points[:, 1]))]
    handle = live.grab(tuple(hem), radius_mm=50.0)
    live.drag(handle, (hem[0], hem[1] + 0.02, hem[2]))
    live.release(handle, frames=20)
    rate = live.rate()
    assert rate["steps"] == 1 and rate["settles"] == 1
    assert rate["ms_per_settle"] > rate["ms_per_step"] * 3


def test_a_grip_is_feathered_rather_than_clamped(draped) -> None:
    """Fingers are not clamps, and a hard edge shows up as a crease nobody
    put there."""
    garment, field = _fresh(draped)
    live = LiveSession(garment, field, fabric="cotton_poplin")
    hem = garment.points[int(np.argmin(garment.points[:, 1]))]
    handle = live.grab(tuple(hem), radius_mm=60.0)
    assert len(handle) > 3
    assert handle.weights.max() == pytest.approx(1.0, abs=0.05)
    assert handle.weights.min() < 0.5
    assert np.all(handle.weights >= 0.0)


def test_grabbing_thin_air_says_how_far_the_cloth_is(draped) -> None:
    garment, field = _fresh(draped)
    live = LiveSession(garment, field, fabric="cotton_poplin")
    with pytest.raises(ValueError, match="the nearest is"):
        live.grab((5.0, 5.0, 5.0), radius_mm=10.0)


def test_a_fold_is_measured_along_the_push_and_not_as_a_distance(draped) -> None:
    """Total displacement is the wrong instrument and said so loudly: every
    fabric came out holding 150-200% of the push, because the settle after
    letting go is mostly the cloth falling. Projecting on the push axis leaves
    gravity out of the number, where it belongs."""
    garment, field = _fresh(draped)
    live = LiveSession(garment, field, fabric="cotton_poplin")
    front = garment.points[int(np.argmax(garment.points[:, 2]))]
    report = live.fold(tuple(front), depth_mm=45.0, direction=(0, 0, -1), radius_mm=55.0, settle=40)
    assert 0.0 < report["held_fraction"] <= 1.05, report
    assert report["pushed_mm"] > 0.0
    # the hand asked for 45 mm and the cloth gave what it gave, which is why
    # `pushed_mm` is reported rather than assumed equal to the request
    assert report["pushed_mm"] < 45.0


def test_easing_a_stitch_moves_the_seam_it_names(draped) -> None:
    """A live stitch adjustment, and the only gesture here that is honestly
    NOT interactive-rate: changing a rest length changes the data the prepared
    graph was built around, so the graph is rebuilt. Nobody scrubs a seam
    allowance at 60 fps."""
    garment, field = _fresh(draped)
    live = LiveSession(garment, field, fabric="cotton_poplin")
    seen = []
    for millimetres in (0.0, 6.0, 6.0, -12.0):
        report = live.ease("side-right", millimetres)
        seen.append((report["rest_mean_mm"], report["this_seam_mean_mm"]))
    rests = [s[0] for s in seen]
    means = [s[1] for s in seen]
    assert rests == [0.0, 6.0, 12.0, 0.0], "eases are cumulative"
    for rest, mean in seen:
        assert mean == pytest.approx(rest, abs=1.0), seen
    assert means[2] > means[0] + 8.0


def test_easing_a_seam_that_is_not_there_names_the_ones_that_are(draped) -> None:
    garment, field = _fresh(draped)
    live = LiveSession(garment, field, fabric="cotton_poplin")
    with pytest.raises(ValueError, match="side-right"):
        live.ease("side-middle", 4.0)


def test_an_animated_wind_does_not_invalidate_the_prepared_graph() -> None:
    """Only the room's CONDITIONING reaches the prepared arrays - temperature,
    humidity and fibre, through the moisture regain that sets particle mass.
    Gravity and wind are applied per call, inside the kernel.

    Keying the cache on the whole room meant an animated wind invalidated it on
    every single frame, which is precisely the case the cache exists for. Found
    by simulating a cape in a gust and watching the solver refuse its own
    prepared graph on frame one.
    """
    from seamkiln.drape.environment import Environment
    from seamkiln.drape.solve import _prepare_key
    from seamkiln.pattern.fabric import fabric as fabric_by_name

    body = mannequin()
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=22.0)
    cloth = fabric_by_name("cotton_poplin")

    def key(room):
        return _prepare_key(garment, cloth, DrapeSettings(environment=room))

    breeze = Environment(wind=(6.0, 0.0, 0.0))
    gale = Environment(wind=(-9.0, 2.0, 3.0), wind_gust=0.6)
    assert key(breeze) == key(gale), "a gust threw the cache away"
    assert key(breeze) == key(Environment(gravity=1.62)), "gravity is a per-call force"
    # ... and what genuinely does change the prepared mass still invalidates it
    assert key(breeze) != key(Environment(humidity=0.95))
    assert key(breeze) != key(Environment(temperature_c=40.0))
