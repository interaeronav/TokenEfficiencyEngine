"""A body that moves INSIDE a drape call, and the static path it must not touch.

The animator used to move the body between calls as a jump: rebake, teleport
the garment, solve on a body standing still. Each jump up into the cloth
resolved as a full push in one substep - a kick of tens of metres per second
- and nothing on the way down pulled the cloth back, so a jersey tee rode up
16 mm per walking stride and 40 per running stride. The kernel now takes a
per-substep schedule of the body's placement and, for a deforming body, a
second field on the same lattice blended across the call. Every number
below is measured on the kernel alone, with no animator in the way.
"""

from __future__ import annotations

import numpy as np
import pytest
import trimesh

from seamkiln.drape.body import BodyMotion, mannequin, sdf_from_mesh, solid_ball
from seamkiln.drape.garment import Placement, build_garment, top_arrangement
from seamkiln.drape.solve import DrapeSettings, drape
from seamkiln.pattern.fixtures import tee_block
from seamkiln.pattern.geometry import Vertex
from seamkiln.pattern.model import Panel, Pattern

FLAT = np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])  # laid flat, y up


def _square(side_mm: float = 240.0) -> Pattern:
    half = side_mm / 2
    return Pattern(
        name="square",
        panels=[
            Panel(
                id="SQ",
                outline=[
                    Vertex(-half, -half),
                    Vertex(half, -half),
                    Vertex(half, half),
                    Vertex(-half, half),
                ],
            )
        ],
        units="mm",
    )


def _square_on(centre, *, height_above: float = 0.16, pd: float = 12.0):
    origin = np.asarray(centre, dtype=np.float64) + np.asarray([0.0, height_above, 0.0])
    return build_garment(
        _square(),
        {"SQ": Placement(flat=True, rotation=FLAT, origin_m=origin)},
        particle_distance=pd,
    )


def _slab(centre=(0.0, 0.0, 0.0), extents=(0.6, 0.1, 0.6), voxel_mm: float = 10.0):
    box = trimesh.creation.box(extents=extents)
    box.apply_translation(np.asarray(centre, dtype=np.float64))
    return sdf_from_mesh(box, voxel_mm=voxel_mm)


def _smoothstep_motion(field, delta, steps: int) -> BodyMotion:
    """A rigid translation by `delta` over the call with zero end velocities."""
    end = field.moved(delta, relative=True)
    motion = BodyMotion.between(field, end, steps=steps)
    u = np.linspace(0.0, 1.0, steps + 1)
    ease = u * u * (3.0 - 2.0 * u)
    motion.translation = np.ascontiguousarray(
        field.translation[None, :] + np.asarray(delta, dtype=np.float64)[None, :] * ease[:, None]
    )
    motion.translation[0] = field.translation
    motion.translation[-1] = end.translation
    return motion


# -- the static path -----------------------------------------------------------


def test_a_static_drape_is_bit_identical_with_and_without_a_motion_schedule() -> None:
    """The law this file is built round. Not "equal to within zero arithmetic":
    the static path executes the old instruction sequence, and a schedule that
    never varies is not `moving`, so the kernel reads none of it."""
    body = mannequin()
    field = sdf_from_mesh(body, voxel_mm=12.0)
    pattern = tee_block()
    settings = DrapeSettings(frames=40)
    steps = settings.frames * settings.substeps
    prints = {}
    points = {}
    for label, motion in (
        ("plain", None),
        ("static", BodyMotion.static(field, steps)),
        ("between the same", BodyMotion.between(field, field, steps)),
    ):
        garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=25.0)
        result = drape(garment, field, settings=settings, motion=motion)
        prints[label] = result.fingerprint
        points[label] = result.points
        assert result.report().get("body_motion") is None, label
    assert prints["plain"] == prints["static"] == prints["between the same"], prints
    for label in ("static", "between the same"):
        assert float(np.abs(points["plain"] - points[label]).max()) == 0.0, label


def test_a_bake_on_a_wider_lattice_reads_the_same_distances() -> None:
    body = mannequin()
    own = sdf_from_mesh(body, voxel_mm=12.0)
    wide = sdf_from_mesh(body, voxel_mm=12.0, bounds=(body.bounds[0] - 0.2, body.bounds[1] + 0.3))
    assert wide.grid.shape != own.grid.shape
    rng = np.random.default_rng(7)
    pts = rng.uniform(body.bounds[0], body.bounds[1], size=(2000, 3))
    assert float(np.abs(own.sample(pts) - wide.sample(pts)).max()) < 1e-9
    with pytest.raises(ValueError, match="leaves the lattice"):
        sdf_from_mesh(body, voxel_mm=12.0, bounds=(body.bounds[0] + 0.3, body.bounds[1] - 0.3))


def test_a_motion_is_refused_when_it_does_not_fit_the_call() -> None:
    body = mannequin()
    field = sdf_from_mesh(body, voxel_mm=12.0)
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=25.0)
    settings = DrapeSettings(frames=2, substeps=4)
    wrong_length = BodyMotion.between(field, field.moved([0.1, 0.0, 0.0]), steps=5)
    with pytest.raises(ValueError, match="spans 5 substeps"):
        drape(garment, field, settings=settings, motion=wrong_length)
    elsewhere = field.moved([0.0, 0.0, 0.2])
    not_from_here = BodyMotion.between(elsewhere, elsewhere.moved([0.1, 0.0, 0.0]), steps=8)
    with pytest.raises(ValueError, match="does not start where the body is"):
        drape(garment, field, settings=settings, motion=not_from_here)
    other_lattice = sdf_from_mesh(
        body, voxel_mm=12.0, bounds=(body.bounds[0] - 0.1, body.bounds[1] + 0.1)
    )
    with pytest.raises(ValueError, match="one lattice"):
        BodyMotion.between(field, other_lattice, steps=8)


# -- the physics, on a rigid slab ---------------------------------------------


@pytest.fixture(scope="module")
def resting():
    """A poplin square settled on a slab: the starting state for every push."""
    field = _slab()
    garment = _square_on((0.0, 0.05, 0.0), height_above=0.03)
    result = drape(
        garment, field, fabric="cotton_poplin", settings=DrapeSettings(frames=90, substeps=12)
    )
    return field, garment, result.points.copy(), result.velocity.copy()


def test_a_body_accelerating_gently_carries_resting_cloth(resting) -> None:
    """Coulomb's static regime, relative to the BODY: a slab that eases to
    0.15 m over a second (peak 0.9 m/s^2, under mu g = 3.4) takes the cloth
    with it and leaves it moving at the slab's speed."""
    field, garment, rest, velocity = resting
    garment.points = rest.copy()
    settings = DrapeSettings(frames=60, substeps=12)
    motion = _smoothstep_motion(field, [0.15, 0.0, 0.0], settings.frames * settings.substeps)
    result = drape(
        garment, field, fabric="cotton_poplin", settings=settings, velocity=velocity, motion=motion
    )
    carried = float(result.points[:, 0].mean() - rest[:, 0].mean())
    assert abs(carried - 0.15) < 0.005, f"carried {carried * 1000:.1f} mm of 150"
    assert result.contact["worn"] is True
    assert result.report()["body_motion"]["travel_mm"] == pytest.approx(150.0, abs=0.1)


def test_a_body_snatched_away_slides_out_from_under_the_cloth(resting) -> None:
    """The same 0.15 m in a fifth of a second (peak 22 m/s^2, far over mu g):
    friction can no longer keep up and the cloth is left behind. Coulomb's
    regime change, measured."""
    field, garment, rest, velocity = resting
    garment.points = rest.copy()
    settings = DrapeSettings(frames=12, substeps=12)
    motion = _smoothstep_motion(field, [0.15, 0.0, 0.0], settings.frames * settings.substeps)
    result = drape(
        garment, field, fabric="cotton_poplin", settings=settings, velocity=velocity, motion=motion
    )
    carried = float(result.points[:, 0].mean() - rest[:, 0].mean())
    assert carried < 0.10, f"the cloth followed a snatched slab by {carried * 1000:.0f} mm"


def test_a_body_bobbing_under_cloth_does_not_ratchet_it_up(resting) -> None:
    """The mechanism behind the ride-up, isolated: a slab oscillating 25 mm at
    2 Hz (a walk's pelvis) for two seconds across 24 calls, motion and velocity
    carried between them. The cloth's height above the slab stays put and the
    cloth ends where it started."""
    field, garment, rest, velocity = resting
    garment.points = rest.copy()
    settings = DrapeSettings(frames=5, substeps=12)
    steps = settings.frames * settings.substeps
    amplitude, hz = 0.025, 2.0
    frame_s = settings.frames * settings.dt
    placed = field
    elapsed = 0.0
    heights = []
    for _call in range(24):
        times = elapsed + np.linspace(0.0, frame_s, steps + 1)
        y = amplitude * np.sin(2.0 * np.pi * hz * times)
        end = field.moved([0.0, float(y[-1]), 0.0])
        motion = BodyMotion.between(placed, end, steps=steps)
        motion.translation = np.ascontiguousarray(
            np.stack([np.zeros_like(y), y, np.zeros_like(y)], axis=1) + field.translation[None, :]
        )
        motion.translation[0] = placed.translation
        motion.translation[-1] = end.translation
        result = drape(
            garment,
            placed,
            fabric="cotton_poplin",
            settings=settings,
            velocity=velocity,
            motion=motion,
        )
        garment.points = result.points
        velocity = result.velocity
        placed = end
        elapsed = float(times[-1])
        heights.append(float(result.points[:, 1].mean() - (0.05 + 0.05 + float(y[-1]))))
    heights = np.asarray(heights)
    assert float(heights.max() - heights.min()) < 0.010, (
        f"height wandered {heights.max() - heights.min():.3f}"
    )
    settled_back = float(garment.points[:, 1].mean() - rest[:, 1].mean() - float(y[-1]))
    assert abs(settled_back) < 0.003, (
        f"the cloth ended {settled_back * 1000:.1f} mm from where it started"
    )


def test_a_body_moving_away_leaves_cloth_to_fall_and_never_pulls_it(resting) -> None:
    """A push is transmitted; a pull is not. A slab descending at 0.3 m/s for
    half a second outruns nothing - the cloth falls after it under gravity and
    ends on it, never above where it started."""
    field, garment, rest, velocity = resting
    garment.points = rest.copy()
    settings = DrapeSettings(frames=30, substeps=12)
    end = field.moved([0.0, -0.15, 0.0])
    motion = BodyMotion.between(field, end, steps=settings.frames * settings.substeps)
    result = drape(
        garment, field, fabric="cotton_poplin", settings=settings, velocity=velocity, motion=motion
    )
    assert float(result.points[:, 1].max()) <= float(rest[:, 1].max()) + 0.002
    assert result.contact["touching_fraction"] > 0.5, result.contact


# -- symmetry and determinism --------------------------------------------------


def test_a_moving_ball_has_no_favourite_direction() -> None:
    """A ball sliding +x under a square on the right of the origin and a ball
    sliding -x under the same square on the left must leave mirror-image
    landings - the static mirror test, with the body in motion."""
    from scipy.spatial import cKDTree

    settings = DrapeSettings(frames=90, substeps=12)
    steps = settings.frames * settings.substeps
    landed = {}
    for sign in (-1.0, 1.0):
        centre = np.asarray([sign * 0.31, 0.30, 0.0])
        field = sdf_from_mesh(solid_ball(radius_m=0.09, centre=tuple(centre)), voxel_mm=13.0)
        garment = _square_on(centre)
        motion = _smoothstep_motion(field, [sign * 0.05, 0.0, 0.0], steps)
        result = drape(garment, field, fabric="cotton_poplin", settings=settings, motion=motion)
        landed[sign] = result.points - (centre + np.asarray([sign * 0.05, 0.0, 0.0]))
    mirrored = landed[-1.0] * np.asarray([-1.0, 1.0, 1.0])
    gap, _ = cKDTree(landed[1.0]).query(mirrored)
    assert gap.mean() * 1000.0 < 3.0, f"mean mirror gap {gap.mean() * 1000:.1f} mm"
    assert gap.max() * 1000.0 < 15.0, f"max mirror gap {gap.max() * 1000:.1f} mm"


def test_a_growing_ball_is_a_surface_that_moves_through_the_frame() -> None:
    """Two fields on one lattice, blended: a ball growing from 90 to 100 mm
    under a square lifts it ~10 mm over the call, and the mirror of that
    landing is the landing of the mirrored growth."""
    from scipy.spatial import cKDTree

    settings = DrapeSettings(frames=60, substeps=12)
    steps = settings.frames * settings.substeps
    landed = {}
    for sign in (-1.0, 1.0):
        centre = np.asarray([sign * 0.31, 0.30, 0.0])
        bounds = (centre - 0.16, centre + 0.16)
        small = sdf_from_mesh(
            solid_ball(radius_m=0.09, centre=tuple(centre)), voxel_mm=13.0, bounds=bounds
        )
        large = sdf_from_mesh(
            solid_ball(radius_m=0.10, centre=tuple(centre)), voxel_mm=13.0, bounds=bounds
        )
        garment = _square_on(centre)
        settled = drape(
            garment, small, fabric="cotton_poplin", settings=DrapeSettings(frames=60, substeps=12)
        )
        garment.points = settled.points.copy()
        motion = BodyMotion.between(small, large, steps=steps)
        assert motion.blend and motion.moving
        result = drape(
            garment,
            small,
            fabric="cotton_poplin",
            settings=settings,
            velocity=settled.velocity,
            motion=motion,
        )
        lifted = float(result.points[:, 1].max() - settled.points[:, 1].max())
        assert 0.005 < lifted < 0.020, f"the crown lifted {lifted * 1000:.1f} mm for 10 of growth"
        assert result.report()["body_motion"]["blend"] is True
        landed[sign] = result.points - centre
    mirrored = landed[-1.0] * np.asarray([-1.0, 1.0, 1.0])
    gap, _ = cKDTree(landed[1.0]).query(mirrored)
    assert gap.mean() * 1000.0 < 3.0, f"mean mirror gap {gap.mean() * 1000:.1f} mm"


def test_a_moving_drape_reproduces_itself() -> None:
    field = _slab()
    settings = DrapeSettings(frames=30, substeps=12)
    prints = set()
    for _ in range(2):
        garment = _square_on((0.0, 0.05, 0.0), height_above=0.03)
        motion = _smoothstep_motion(field, [0.05, 0.0, 0.02], settings.frames * settings.substeps)
        prints.add(
            drape(
                garment, field, fabric="cotton_poplin", settings=settings, motion=motion
            ).fingerprint
        )
    assert len(prints) == 1
    first = BodyMotion.between(field, field.moved([0.1, 0.0, 0.0]), steps=24)
    second = BodyMotion.between(field, field.moved([0.1, 0.0, 0.0]), steps=24)
    assert first.translation.tobytes() == second.translation.tobytes()


def test_restitution_is_dormant_and_this_says_so() -> None:
    """The restitution block writes a velocity that the substep's own
    write-back overwrites, so every card's 0.02 does nothing. Its relative
    form is in place for the day it is revived; this test is the alarm that
    goes off when it is, because that day every fabric changes."""
    from seamkiln.materials import derive

    body = mannequin()
    field = sdf_from_mesh(body, voxel_mm=12.0)
    pattern = tee_block()
    prints = set()
    for bounce in (0.0, 0.9):
        card = derive("cotton_poplin", f"poplin-r{bounce}", restitution=bounce)
        garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=25.0)
        prints.add(
            drape(garment, field, fabric=card, settings=DrapeSettings(frames=30)).fingerprint
        )
    assert len(prints) == 1, "restitution has come alive: re-run the BS 5058 battery"
