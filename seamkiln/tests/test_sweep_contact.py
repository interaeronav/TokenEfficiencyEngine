"""A limb sweeping into cloth that is held: the sheet is pushed ahead of the
body or wraps it, never straddled and never carried inside.

On a run, three or four particles a cycle ended 8-38 mm inside the body,
at any substep count and any frame rate. Replayed stage by stage they were
sliver-fringe outline vertices at the crease of the shoulder ball and the
arm: thrown 20 mm into the body by their 2.5 mm rest edges, pushed out by
the collision (+2.9 mm), and put straight back in by FRICTION, whose tangent
plane came from the normal at the pre-push point 20 mm inside the union,
97 degrees off the surface. The fix takes friction's plane from the pushed
point. These tests hold the door: T3 is the measured mechanism, T1 and T2
guard a genuine sweep-through, rigid and blended.
"""

from __future__ import annotations

import numpy as np
import pytest
import trimesh

from seamkiln.drape.body import BodyMotion, sdf_from_mesh, solid_ball
from seamkiln.drape.cusick import specimen
from seamkiln.drape.garment import Placement, build_garment
from seamkiln.drape.solve import DrapeSettings, drape
from seamkiln.pattern.geometry import Vertex
from seamkiln.pattern.model import Panel, Pattern

VOXEL_MM = 10.0
# the sheet stands in the plane x = 0, facing a body that comes along +x
UPRIGHT = np.asarray([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
FLAT = np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])


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


def _curtain(centre_y: float = 0.30):
    """A poplin square standing upright with its top and bottom rows pinned."""
    garment = build_garment(
        _square(),
        {"SQ": Placement(flat=True, rotation=UPRIGHT, origin_m=np.asarray([0.0, centre_y, 0.0]))},
        particle_distance=12.0,
    )
    pins = (np.abs(garment.points[:, 1] - centre_y) > 0.112).astype(np.float64)
    assert 20 < pins.sum() < 60
    return garment, pins


def _smooth(field, delta, steps: int) -> BodyMotion:
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


def _fringe(garment) -> np.ndarray:
    """The outline's sliver vertices: any particle on a rest edge under two
    thirds of the particle distance (the specimen's outline runs at 5.2 mm on
    a 12 mm mesh)."""
    short = garment.structural[garment.structural_rest < 0.008]
    return np.unique(short)


def test_t1_a_slab_sweeping_into_a_held_sheet_pushes_it_ahead() -> None:
    """Rigid schedule. A slab whose leading face starts 30 mm behind the
    sheet advances 60 mm through the sheet's plane over one call. The sheet
    bulges ahead of the face in the slab's band and no particle is left
    inside the slab or beyond its far face."""
    slab = trimesh.creation.box(extents=(0.10, 0.10, 0.30))
    slab.apply_translation([-0.08, 0.30, 0.0])  # leading face at x = -0.03
    field = sdf_from_mesh(slab, voxel_mm=VOXEL_MM)
    garment, pins = _curtain()
    settings = DrapeSettings(frames=30, substeps=12)
    motion = _smooth(field, [0.06, 0.0, 0.0], settings.frames * settings.substeps)
    result = drape(
        garment, field, fabric="cotton_poplin", settings=settings, pins=pins, motion=motion
    )
    report = result.report()
    assert report["penetration"]["deepest_penetration_mm"] < VOXEL_MM, report["penetration"]
    band = np.abs(result.points[:, 1] - 0.30) < 0.045
    ahead = result.points[band, 0]
    assert ahead.min() > 0.006 - 0.005, (
        f"a particle sits {(0.03 - ahead.min()) * 1000:.1f} mm inside the face"
    )
    assert (result.points[:, 0] > -0.07).all(), "a particle passed through to the slab's far side"


def test_t2_a_blended_capsule_sweeping_into_a_held_sheet_pushes_it_ahead() -> None:
    """The two-field blend: a capsule baked at two positions 36 mm apart on
    one lattice, the schedule blending between them. Same claim as T1.

    The sweep sits inside the blend's own envelope, 2 sqrt(voxel R) = 40 mm
    for this 40 mm capsule on a 10 mm voxel. Outside it the blend is not a
    moving capsule: at 60 mm the two fields' gradients cancel between the
    positions and ten particles end 10.3 mm inside - the same number before
    and after the friction-plane fix, because no push there is large enough
    to gate it. That is the blend envelope's limit (a rigid move belongs in
    the rigid schedule; a deforming body is sampled finely enough), recorded
    here as the number it fails with, not asserted."""

    def capsule_at(x: float):
        body = trimesh.creation.capsule(height=0.16, radius=0.04)
        body.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1.0, 0.0, 0.0]))
        body.apply_translation([x, 0.30, 0.0])
        return body

    start, end = capsule_at(-0.07), capsule_at(-0.034)  # leading surface -0.03 -> +0.006
    lo = np.minimum(start.bounds[0], end.bounds[0]) - 0.02
    hi = np.maximum(start.bounds[1], end.bounds[1]) + 0.02
    f0 = sdf_from_mesh(start, voxel_mm=VOXEL_MM, bounds=(lo, hi))
    f1 = sdf_from_mesh(end, voxel_mm=VOXEL_MM, bounds=(lo, hi))
    garment, pins = _curtain()
    settings = DrapeSettings(frames=30, substeps=12)
    motion = BodyMotion.between(f0, f1, steps=settings.frames * settings.substeps)
    assert motion.blend is True
    result = drape(garment, f0, fabric="cotton_poplin", settings=settings, pins=pins, motion=motion)
    report = result.report()
    assert report["penetration"]["deepest_penetration_mm"] < VOXEL_MM, report["penetration"]
    # the capsule is round, so "ahead of the face" is a question for the
    # field, not for a plane: nothing inside the end capsule beyond the
    # field's own half-voxel, and nothing past its far side
    inside = -motion.end.sample(result.points) * 1000.0
    assert inside.max() < VOXEL_MM / 2, f"a particle sits {inside.max():.1f} mm inside the capsule"
    assert (result.points[:, 0] > -0.074).all(), (
        "a particle passed through to the capsule's far side"
    )


def test_t3_a_fringe_across_a_crease_stays_on_a_sliding_body() -> None:
    """A guard, not a reproduction: the BS 5058 disc (a curved outline, 180
    vertices at 5 mm on a 12 mm mesh, so a sliver fringe) settles across the
    crease of two overlapping balls, then the body slides 40 mm along the
    crease in one call with friction 0.5. It passed before the friction-plane
    fix as well - the run's mechanism needs the run's throw, which the real
    case below reproduces - and it stays to catch a regression of fringe
    contact on a crease."""
    balls = trimesh.util.concatenate(
        [
            solid_ball(radius_m=0.09, centre=(-0.06, 0.30, 0.0)),
            solid_ball(radius_m=0.09, centre=(0.06, 0.30, 0.0)),
        ]
    )
    field = sdf_from_mesh(balls, voxel_mm=VOXEL_MM)
    # meshed WITHOUT the outline merge: this guard wants the sliver fringe
    # the merge was written to remove (see `resample_closed`)
    garment = build_garment(
        specimen(),
        {"SPECIMEN": Placement(flat=True, rotation=FLAT, origin_m=np.asarray([0.0, 0.45, 0.0]))},
        particle_distance=12.0,
        merge_fraction=0.0,
    )
    fringe = _fringe(garment)
    assert len(fringe) > 100, "the specimen's outline should be a sliver fringe"
    settled = drape(
        garment,
        field,
        fabric="cotton_poplin",
        settings=DrapeSettings(frames=120, substeps=12, friction=0.5),
    )
    garment.points = settled.points.copy()
    settings = DrapeSettings(frames=15, substeps=12, friction=0.5)
    motion = _smooth(field, [0.0, 0.0, 0.04], settings.frames * settings.substeps)
    result = drape(
        garment,
        field,
        fabric="cotton_poplin",
        settings=settings,
        velocity=settled.velocity,
        motion=motion,
    )
    report = result.report()
    depth = -motion.end.sample(result.points[fringe]) * 1000.0
    assert report["penetration"]["deepest_penetration_mm"] < VOXEL_MM, report["penetration"]
    assert depth.max() < VOXEL_MM / 2, f"a fringe vertex ended {depth.max():.1f} mm inside the body"


@pytest.mark.slow
def test_the_run_that_tunnelled_no_longer_does() -> None:
    """The real case, measured: the jersey tee on the posed capsule mannequin
    on a run, one cycle at 24 fps, 24 substeps, a 10 mm voxel. Before the
    friction-plane fix its worst frame put three or four sliver-fringe
    vertices 8-10 mm inside the body at the shoulder-arm crease (28-38 mm
    over three cycles, at every frame rate); after it the worst interval
    reads 0.0-0.7 mm. The bound is a voxel."""
    from seamkiln.avatar import Pose, gait, posed_mannequin, walk
    from seamkiln.drape.garment import top_arrangement
    from seamkiln.pattern.fixtures import tee_block

    body = posed_mannequin(Pose.a_pose())
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=12.0)
    frames = walk(
        garment,
        gait("run", cycles=1.0, samples_per_cycle=8),
        fabric="cotton_jersey",
        fps=24.0,
        voxel_mm=VOXEL_MM,
        settings=DrapeSettings(substeps=24),
    )
    worst = max(f.report["penetration"]["deepest_penetration_mm"] for f in frames)
    assert all(f.report["contact"]["worn"] for f in frames)
    assert worst < VOXEL_MM, f"the run still tunnels: {worst:.1f} mm"
