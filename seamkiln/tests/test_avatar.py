"""Posed bodies, gait, and an avatar you bring yourself.

The blend-shape lane changes a body's SHAPE. This changes its POSE, which is
what a garment mostly cares about: a shirt over a walk is thrown up by the
pelvis and dragged across the back by the arm swing, and none of that happens
when only the phenotype sliders move.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.avatar import (
    GAITS,
    JOINTS,
    Pose,
    adjust,
    custom_avatar,
    describe,
    gait,
    posed_mannequin,
    walk,
)
from seamkiln.drape.garment import build_garment, top_arrangement
from seamkiln.drape.solve import DrapeSettings
from seamkiln.pattern.fixtures import tee_block


@pytest.fixture(scope="module")
def a_pose_body():
    return posed_mannequin(Pose.a_pose())


# Measured drift of the tee's stride-averaged centroid over three strides,
# with the body moving continuously within each frame (see the gait test):
# walk at 12 fps +4.2 mm (per stride +5.0 then -0.8: saturating), run at
# 24 fps -6.0 mm (-2.1, -3.9). The bounds are 1.5 x the measurement with a
# floor of a voxel (10 mm). The run's worst penetration was 27.6 mm at one
# frame per cycle (38, 28, 29, 33 mm at 16, 24, 32, 48 fps): sliver-fringe
# vertices at the shoulder-arm crease, thrown into the body by their 2.5 mm
# rest edges, pushed out by the collision and put straight back by friction,
# whose tangent plane came from the normal at the pre-push point 20 mm inside
# the body. With friction's plane taken at the pushed point, and friction
# never allowed to re-enter, it is 0.0 mm at 24 and 48 fps, 0.14 at 16 and
# 0.0 at 32 (walk 0.0); the bound is a voxel.
# Re-measured 2026-09-04 with the outline merge (the tee's fringe of short
# outline edges gone): the walk +4.8 mm over three strides (+5.4, -0.6), the
# run +18.0 (+12.9, +5.1: decaying). On the fringe-meshed tee they read
# +4.2 (+5.0, -0.8) and -6.0 (-2.1, -3.9). The bounds stay 1.5 x the
# measurement with a floor of a voxel.
WALK_DRIFT_MM = 4.8
RUN_DRIFT_MM = 18.0
WALK_DRIFT_BOUND_MM = 10.0
RUN_DRIFT_BOUND_MM = 27.0
RUN_PENETRATION_BOUND_MM = 10.0


def _tee(body, pd: float = 12.0):
    pattern = tee_block()
    return build_garment(pattern, top_arrangement(pattern, body), particle_distance=pd)


# -- the pose ------------------------------------------------------------------


def test_the_jointed_body_is_not_the_a_pose_mannequin(a_pose_body) -> None:
    """Stated because it would otherwise be assumed. A jointed leg is two
    capsules with a knee between them where the A-pose mannequin's is one, and
    the extra hemisphere makes it 1.811 m against 1.792 m. `mannequin()` is
    left alone rather than delegating here, because every measured number in
    this project belongs to the body that produced it."""
    from seamkiln.drape.body import mannequin

    assert float(a_pose_body.extents[1]) == pytest.approx(1.811, abs=0.01)
    assert float(mannequin().extents[1]) == pytest.approx(1.792, abs=0.01)
    assert a_pose_body.is_watertight


def test_a_flexed_hip_swings_the_knee_forward() -> None:
    """Positive is FLEXION - the limb swings forward, +Z. It is the clinical
    sign convention and the opposite of what looks natural in a 3D package,
    which is exactly why it is asserted rather than assumed."""
    standing = posed_mannequin(Pose())
    flexed = posed_mannequin(Pose(hip_r=45.0, hip_l=45.0))
    assert flexed.bounds[1][2] > standing.bounds[1][2] + 0.2, "the legs did not go forward"
    # ... and lifts the feet, because a swinging leg is shorter vertically
    assert flexed.bounds[0][1] > standing.bounds[0][1]


def test_a_pose_rejects_a_joint_that_does_not_exist() -> None:
    with pytest.raises(ValueError, match="unknown joint"):
        Pose.from_values({"wrist_l": 10.0})
    assert set(Pose().as_values()) == {*JOINTS, "rise_m"}


# -- gait ----------------------------------------------------------------------


def test_a_gait_hits_the_ranges_it_claims() -> None:
    """Every angle here is textbook clinical kinematics for level locomotion,
    not something measured by this project - so the least it can do is
    actually produce the ranges it quotes."""
    for kind in ("walk", "run"):
        spec = GAITS[kind]
        track = gait(kind, cycles=1.0, samples_per_cycle=32)
        hips = [p.hip_r for p in track.poses]
        knees = [p.knee_r for p in track.poses]
        rises = [p.rise_m * 1000.0 for p in track.poses]
        assert min(hips) == pytest.approx(spec.hip_ext, abs=1.0)
        assert max(hips) == pytest.approx(spec.hip_flex, abs=1.0)
        assert max(knees) == pytest.approx(spec.knee_swing, abs=spec.knee_swing * 0.06)
        assert max(rises) - min(rises) == pytest.approx(spec.rise_mm, abs=1.0)
        assert track.duration == pytest.approx(spec.cycle_s, rel=1e-9)


def test_a_run_is_bigger_than_a_walk_in_every_channel() -> None:
    walking, running = GAITS["walk"], GAITS["run"]
    assert running.speed_ms > walking.speed_ms
    assert running.cycle_s < walking.cycle_s  # faster cadence, shorter stride time
    assert running.hip_flex > walking.hip_flex
    assert running.knee_swing > walking.knee_swing
    assert running.shoulder_swing > walking.shoulder_swing
    assert running.trunk_lean > walking.trunk_lean
    assert running.rise_mm > walking.rise_mm


def test_the_legs_are_half_a_cycle_apart_and_the_arms_counter_swing() -> None:
    """The thing everyone animating a walk by hand gets wrong first, and the
    thing a garment notices - counter-rotation is what twists a shirt across
    the back."""
    track = gait("walk", cycles=1.0, samples_per_cycle=32)
    left = np.asarray([p.hip_l for p in track.poses])
    right = np.asarray([p.hip_r for p in track.poses])
    half = len(track.poses) // 2
    assert np.allclose(left[:half], right[half : half * 2], atol=1.0)
    # the arm on a side opposes the leg on that side
    arm = np.asarray([p.shoulder_r for p in track.poses])
    assert float(np.corrcoef(arm, right)[0, 1]) < -0.9


def test_the_pelvis_rises_twice_per_stride() -> None:
    """Once over each stance leg - which is why a walk bounces at double the
    stride frequency, and why a gait that forgets it makes every fabric look
    stiff."""
    track = gait("walk", cycles=1.0, samples_per_cycle=64)
    # one full period, counted CYCLICALLY - the last sample repeats the first,
    # so a straight interior scan misses the peak that sits on the seam
    rise = np.asarray([p.rise_m for p in track.poses])[:-1]
    peaks = int(((rise > np.roll(rise, 1)) & (rise > np.roll(rise, -1))).sum())
    assert peaks == 2, f"{peaks} pelvis peaks in one stride, expected 2"


def test_an_unknown_gait_names_the_known_ones() -> None:
    with pytest.raises(ValueError, match="run"):
        gait("skip")


# -- draping along it ----------------------------------------------------------


def test_cloth_time_is_derived_from_the_frame_rate_and_a_mismatch_is_refused() -> None:
    """The bug this rule exists to stop, with its measured cost. A run at 8 fps
    with the old default of 60 steps gave the cloth 1.0 s of gravity for every
    0.125 s the body moved, and a t-shirt slid 270 MM DOWN the body in one
    stride while every frame still reported worn=True, because it was still
    touching. Accuracy comes from `substeps`; `frames` buys more SECONDS, and
    more seconds than the body took is a different animation, not a better one.
    """
    body = posed_mannequin(Pose.a_pose())
    with pytest.raises(ValueError, match="The garment will slide"):
        walk(_tee(body), gait("walk", cycles=0.25), fps=8.0, frames_per_step=60)


@pytest.mark.slow
def test_a_garment_is_thrown_by_a_gait_and_stays_on(a_pose_body) -> None:
    """What a walk does to a shirt: the hem swings, the shirt stays where it
    is on the body, and it never leaves it. A run swings the hem further than
    a walk, which is the whole reason to model the vertical travel.

    Measured with the body moving continuously within each frame (three
    strides, the tee's centroid averaged over each stride so the bob cancels):
    the walk at 12 fps drifts +4.8 mm over three strides (+5.4 then -0.6: it
    saturates) and the run at 24 fps +18.0 (+12.9, +5.1: decaying) on the
    mesh with its outline fringe merged - +4.2 and -6.0 on the fringed mesh
    the numbers were first taken on; the hem swings 32 mm
    a stride on the walk and 52-99 on the run. With the old animator - the
    body advancing between frames as a jump, each jump up into the cloth a
    full push in one substep - the same tee rode up 16 mm per walking stride
    and 40 per running stride, without saturating: 48 and 120 over these
    three. The bounds are 1.5 x the measured drift with a floor of a voxel;
    the old 120 mm was that artefact's number.

    The run is measured at 24 fps and not 16 because two fields blended
    across a frame pinch a limb of radius R that moves delta by about
    delta^2 / 8R: below the field's half-voxel while delta <= 2 sqrt(voxel R),
    41 mm a frame for a forearm on this 10 mm voxel, which a run's arm
    exceeds at 16 fps. `sweep_mm` on every frame says where a body stands.
    """
    swings: dict[str, float] = {}
    drift: dict[str, float] = {}
    penetration: dict[str, float] = {}
    for kind, fps in (("walk", 12.0), ("run", 24.0)):
        cycles = 3
        track = gait(kind, cycles=float(cycles), samples_per_cycle=8)
        frames = walk(
            _tee(a_pose_body),
            track,
            fabric="cotton_jersey",
            fps=fps,
            voxel_mm=10.0,
            settings=DrapeSettings(substeps=24),
        )
        assert all(f.report["contact"]["worn"] for f in frames), f"{kind}: it came off"
        times = np.array([f.time_s for f in frames])
        centroid = np.array([float(f.points[:, 1].mean()) for f in frames])
        hem = np.array([float(f.points[:, 1].min()) for f in frames])
        period = track.duration / cycles
        means, hem_swings = [], []
        for k in range(cycles):
            window = (times >= k * period - 1e-9) & (times < (k + 1) * period - 1e-9)
            means.append(float(centroid[window].mean()))
            hem_swings.append(float(hem[window].max() - hem[window].min()))
        drift[kind] = (means[-1] - means[0]) * 1000.0
        swings[kind] = float(np.mean(hem_swings)) * 1000.0
        penetration[kind] = max(f.report["penetration"]["deepest_penetration_mm"] for f in frames)
    assert abs(drift["walk"]) < WALK_DRIFT_BOUND_MM, (
        f"walk: the shirt travelled {drift['walk']:.0f} mm"
    )
    assert abs(drift["run"]) < RUN_DRIFT_BOUND_MM, f"run: the shirt travelled {drift['run']:.0f} mm"
    # A run swings the hem MORE than a walk.
    assert swings["run"] > swings["walk"], swings
    assert penetration["walk"] <= 10.0, penetration
    assert penetration["run"] < RUN_PENETRATION_BOUND_MM, penetration


# -- bring your own body -------------------------------------------------------


def test_an_avatar_in_centimetres_is_rescaled_and_says_so(tmp_path, a_pose_body) -> None:
    """The failure mode this is built against is SILENT: an avatar exported in
    centimetres arrives 100x too big, the garment is a postage stamp on it,
    every seam closes perfectly, and the fit report is full of confident
    numbers about a garment that would fit a doll."""
    big = a_pose_body.copy()
    big.apply_scale(100.0)  # metres -> centimetres
    path = tmp_path / "avatar_cm.obj"
    big.export(path)

    loaded = custom_avatar(path)
    assert float(loaded.extents[1]) == pytest.approx(1.811, abs=0.02)
    info = describe(loaded)
    assert info["units_in"] == "cm"
    assert any("reads as cm" in n for n in info["notes"])
    # and it is standing on the floor at the origin, like every body here
    assert float(loaded.bounds[0][1]) == pytest.approx(0.0, abs=1e-6)


def test_a_z_up_avatar_is_turned_upright(tmp_path, a_pose_body) -> None:
    import trimesh

    lying = a_pose_body.copy()
    lying.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1.0, 0.0, 0.0]))
    path = tmp_path / "avatar_zup.obj"
    lying.export(path)
    loaded = custom_avatar(path)
    assert int(np.argmax(loaded.extents)) == 1, "still lying down"
    assert any("Z-up" in n for n in describe(loaded)["notes"])


def test_something_that_is_not_a_body_is_refused(tmp_path) -> None:
    """Refusing beats draping onto it: a wrongly-scaled avatar produces a
    perfect-looking fit report about nothing."""
    import trimesh

    path = tmp_path / "planet.obj"
    trimesh.creation.cylinder(radius=900.0, height=4000.0).export(path)
    with pytest.raises(ValueError, match="which is not a body"):
        custom_avatar(path)


def test_height_and_girth_adjust_separately(a_pose_body) -> None:
    """Separately, because they are separate on a body. Scaling a whole avatar
    to change its height also changes every circumference, which turns a taller
    person into a bigger one - and the garment that fits that is not the
    garment that fits the taller person."""
    taller = adjust(a_pose_body, height_m=1.95)
    assert float(taller.extents[1]) == pytest.approx(1.95, abs=1e-3)
    assert float(taller.extents[0]) == pytest.approx(float(a_pose_body.extents[0]), rel=1e-6)

    wider = adjust(a_pose_body, girth_scale=1.15)
    assert float(wider.extents[1]) == pytest.approx(float(a_pose_body.extents[1]), rel=1e-6)
    assert float(wider.extents[0]) == pytest.approx(float(a_pose_body.extents[0]) * 1.15, rel=1e-6)
