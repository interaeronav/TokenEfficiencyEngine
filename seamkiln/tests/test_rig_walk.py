"""A brought-in body that ARTICULATES: linear blend skinning, end to end.

The defect this closes is measurable and was measured: `avatar.custom_avatar`
loads a body with `trimesh.load(force="mesh")`, which flattens a scene to one
mesh and throws the skeleton away, so `session.walk` falls back to
`rigid_factory` and the finest rigged character in the world walks as a
statue. The contrast test below is the deliverable: on the RIGID path a hand,
a foot and the pelvis all move exactly the same distance per frame - that is
what a statue is - while on the articulated path the foot moves 8x the
pelvis.

Every number here was measured on this machine against the character
`rig.character` authors (stature 1.80 m, `cells_tall=48`, 11,756 triangles),
because a fixture has to be deterministic, licence-clean and runnable in CI:
the owner's asset folder holds only obfuscated CLO `.avt` payloads, and SMPL /
SMPL-X / STAR are non-commercial (research doc 67 section 2).
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pytest

from seamkiln.animation import animation_report
from seamkiln.avatar import (
    Pose,
    custom_avatar,
    gait,
    rigged_avatar,
    rigged_factory,
    rigid_factory,
    walk,
)
from seamkiln.drape.dressing import frame_from_mesh, wrap_arrangement
from seamkiln.drape.garment import build_garment
from seamkiln.drape.solve import DrapeSettings
from seamkiln.pattern.fixtures import tee_block
from seamkiln.rig.character import build_character
from seamkiln.rig.gltf_read import RigReadError
from seamkiln.rig.skin import RigSkinError
from seamkiln.session import Command, Session

H = 1.80
# 48 cells, not the character's default 60: 11,756 triangles against the
# figure's 9,760, which is what a walk test can afford to rebake a collision
# field from once per frame. The rig is the thing under test, not the mesh
# resolution, and the skeleton does not change with it.
CELLS = 48


@pytest.fixture(scope="module")
def character_glb(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp("rig") / "character.glb"
    build_character(H, cells_tall=CELLS).to_glb(path)
    return str(path)


@pytest.fixture(scope="module")
def body(character_glb: str):
    return rigged_avatar(character_glb)


# -- the skin itself -----------------------------------------------------------


def test_the_bind_pose_is_the_identity(body) -> None:
    """`inverse_bind @ rest == I`, or every vertex drifts before anything moves.

    Measured 5.2e-5 mm, which is float32 accessor storage on a 1.8 m body and
    not the arithmetic: the same check in float64 is exact.
    """
    drift = np.abs(body.posed_vertices(Pose()) - body.rest_vertices).max()
    assert drift * 1000.0 < 1.0e-3, f"the bind pose moved {drift * 1000:.4g} mm"


def test_flexion_swings_every_limb_the_way_the_mannequin_does(body) -> None:
    """The signs, pinned. A limb that bends the wrong way reads as a solver
    bug three hours downstream, and no other test in this suite would catch
    it: the mesh stays watertight, the garment stays worn, the report is full
    of confident numbers about a body walking with its knees in front.

    seamkiln's convention (`avatar._swing`): positive is FLEXION, the limb
    swings toward +Z. Knee and elbow are subtracted from their parent's angle,
    so they bend the limb BACK. The trunk is the third case - the spine points
    up, so a forward lean carries the head forward and the hanging hand back.
    """
    rest = body.rest_vertices
    foot, hand, head = (body.vertices_of(n) for n in ("LeftFoot", "LeftHand", "Head"))

    def dz(pose: Pose, which: np.ndarray) -> float:
        moved = body.posed_vertices(pose)
        return float((moved[which].mean(axis=0) - rest[which].mean(axis=0))[2]) * 1000.0

    assert dz(Pose(hip_l=30.0), foot) == pytest.approx(413.4, abs=1.0)  # forward
    assert dz(Pose(knee_l=60.0), foot) == pytest.approx(-394.8, abs=1.0)  # back
    assert dz(Pose(shoulder_l=30.0), hand) == pytest.approx(279.6, abs=1.0)  # forward
    assert dz(Pose(elbow_l=60.0), hand) == pytest.approx(-285.1, abs=1.0)  # back
    assert dz(Pose(trunk_lean=10.0), head) == pytest.approx(104.7, abs=1.0)  # forward
    # and the other side is the mirror of it, to the last millimetre
    right = body.vertices_of("RightFoot")
    assert dz(Pose(hip_r=30.0), right) == pytest.approx(dz(Pose(hip_l=30.0), foot), abs=0.5)


def test_a_posed_body_is_still_a_body(body) -> None:
    """LBS at the extremes of a walk must not tear the surface: the collision
    field is baked from it, and a hole in the mesh is a hole in the body."""
    posed = body.mesh(Pose(hip_l=30.0, knee_r=60.0, shoulder_l=-20.0, elbow_l=20.0, trunk_lean=5.0))
    rest = body.mesh()
    assert posed.is_watertight
    assert len(posed.faces) == len(rest.faces)
    # volume is conserved to within the pinch a linear blend costs at a joint
    assert posed.volume == pytest.approx(rest.volume, rel=0.03)


def test_loading_the_same_file_twice_gives_the_same_body(character_glb: str) -> None:
    """Determinism is a feature: the same file poses to the same bytes."""
    a, b = rigged_avatar(character_glb), rigged_avatar(character_glb)
    pose = Pose(hip_l=17.0, knee_r=41.0, trunk_lean=3.0)
    assert a.posed_vertices(pose).tobytes() == b.posed_vertices(pose).tobytes()


# -- the deliverable: articulated against rigid --------------------------------


def _worlds(factory, samples) -> list[np.ndarray]:
    """Each frame's body in the world - the mesh plus the factory's offset,
    which is exactly what `animation.animate` hands the collision field."""
    out = []
    for _, values in samples:
        mesh, offset = factory(values)
        out.append(np.asarray(mesh.vertices) + np.asarray(offset))
    return out


def test_a_rigged_body_articulates_where_a_rigless_one_is_a_statue(body) -> None:
    """The measurement that says the campaign worked.

    Per frame of a walk, on this machine: RIGID moves the pelvis, the hand and
    the foot 15.38 mm each - the same number three times, because one piece
    moving is all a rigid body can do. ARTICULATED moves the pelvis 32.3 mm,
    the hand 88.0 and the foot 269.5, which is a body walking.
    """
    samples = gait("walk", cycles=1.0, samples_per_cycle=8).sample(12.0)
    hips, hand, foot = (body.vertices_of(n) for n in ("Hips", "LeftHand", "LeftFoot"))

    def steps(factory) -> tuple[float, float, float]:
        worlds = _worlds(factory, samples)
        moves = [
            [
                float(np.linalg.norm(b[w].mean(axis=0) - a[w].mean(axis=0)))
                for w in (hips, hand, foot)
            ]
            for a, b in pairwise(worlds)
        ]
        return tuple(np.asarray(moves).max(axis=0) * 1000.0)

    r_hips, r_hand, r_foot = steps(rigid_factory(body.mesh()))
    assert r_hips == pytest.approx(r_hand, abs=1e-6) and r_hips == pytest.approx(r_foot, abs=1e-6)
    assert r_hips == pytest.approx(15.38, abs=0.2), "the rigid body's only motion is its rise"

    a_hips, a_hand, a_foot = steps(rigged_factory(body))
    assert a_hips == pytest.approx(32.3, abs=2.0)
    assert a_hand == pytest.approx(88.0, abs=4.0)
    assert a_foot == pytest.approx(269.5, abs=8.0)
    # the contrast itself, stated as the thing that must never regress
    assert a_foot > 5.0 * a_hips, f"foot {a_foot:.1f} mm vs pelvis {a_hips:.1f} mm is a statue"
    assert a_hand > 2.0 * a_hips


def test_the_pelvis_rises_because_the_stance_leg_straightens(body) -> None:
    """Not because anyone scripted it: `rigged_factory` drops the gait's own
    `rise_m` and plants the lowest point on the ground each frame, the same
    choice `figure_factory` makes. Measured 42.4 mm peak to peak over one
    stride (the figure gets 76 mm, the gait scripts 50 mm for a body that
    cannot bend a knee), and it happens TWICE per stride - once over each
    stance leg - which is what throws a garment.
    """
    samples = gait("walk", cycles=1.0, samples_per_cycle=8).sample(12.0)
    hips = body.vertices_of("Hips")
    y = [w[hips, 1].mean() for w in _worlds(rigged_factory(body), samples)]
    rise_mm = (max(y) - min(y)) * 1000.0
    assert rise_mm == pytest.approx(42.4, abs=4.0)
    # feet on the floor throughout: a body that sinks is a body the cloth
    # cannot rest on
    assert all(abs(float(w[:, 1].min())) < 1e-9 for w in _worlds(rigged_factory(body), samples))


def test_cloth_travels_at_the_gaits_own_speed_on_a_rigged_character(body) -> None:
    """The acceptance: a real rigged body, worn on every frame, travelling at
    the gait's speed and not at one picked to frame a shot. Measured 1.234 m/s
    against the walk gait's 1.35 - the same 8 % the figure loses, because the
    cloth's centroid lags the body it is dragged by over a fifth of a stride.
    """
    pattern = tee_block(half_chest=300.0)
    frame = frame_from_mesh(body.mesh())
    garment = build_garment(
        pattern, wrap_arrangement(pattern, frame, height=H), particle_distance=18.0
    )
    frames = walk(
        garment,
        gait("walk", cycles=0.4, samples_per_cycle=8),
        fabric="cotton_jersey",
        fps=12.0,
        voxel_mm=14.0,
        body_factory=rigged_factory(body),
        settings=DrapeSettings(substeps=18),
        travel=True,
    )
    z = [float(f.points[:, 2].mean()) for f in frames]
    speed = (z[-1] - z[0]) / max(frames[-1].time_s, 1e-9)
    assert speed == pytest.approx(1.35, rel=0.15), f"cloth travelled at {speed:.2f} m/s"
    report = animation_report(frames)
    assert report["worn_throughout"] is True
    assert report["worst_penetration_mm"] < 1.0


# -- the refusals, and the fallback that must not change -----------------------


def test_a_file_with_no_skin_refuses_instead_of_returning_a_statue(
    body, tmp_path, character_glb: str
) -> None:
    """The whole point: silence here is what produced a rigid walk. The mesh
    loader still reads this file happily - that is the trap, and the refusal
    is what makes it visible."""
    flat = tmp_path / "norig.glb"
    body.mesh().export(flat)
    with pytest.raises(RigReadError) as caught:
        rigged_avatar(flat)
    message = str(caught.value)
    assert "no skinned node" in message and "Fix:" in message
    # ... while the same file loads fine as an unrigged body, which is exactly
    # how a studio ends up walking a statue without being told
    assert float(custom_avatar(flat).extents[1]) == pytest.approx(H, abs=1e-3)
    assert rigged_avatar(character_glb).describe()["joints"] == 19


def test_a_body_with_no_rig_still_walks_rigidly_and_still_says_so(character_glb: str) -> None:
    """The existing fallback, unchanged: a body kind the session cannot
    articulate travels as one piece and the note says which body kind to use.
    Asserted through the SESSION, because that is where the note lives and
    where a regression would actually be felt.
    """
    s = Session()
    s.apply(Command("block", {"block": "tee", "half_chest": 300.0}))
    s.apply(Command("body", {"kind": "custom", "path": character_glb, "stature_m": H}))
    s.apply(Command("arrange", {"particle_distance_mm": 18.0, "dress": False}))
    s.fabric = "cotton_jersey"
    out = s.apply(
        Command(
            "walk",
            {
                "gait": "walk",
                "cycles": 0.3,
                "fps": 12.0,
                "travel": True,
                "voxel_mm": 16.0,
                "substeps": 12,
            },
        )
    )
    assert out["body"] == "custom"
    assert out["note"] == (
        "a 'custom' body has no joints to swing, so it travels as one piece "
        "with the gait's rise; use body kind 'figure' for articulated limbs"
    )
    assert out["worn_throughout"] is True


def test_an_avatar_in_centimetres_is_caught_the_way_custom_avatar_catches_it(tmp_path) -> None:
    """A body exported at 100x is the silent failure: every seam closes, the
    fit report is confident, and the garment would fit a doll."""
    path = tmp_path / "big.glb"
    build_character(180.0, cells_tall=24).to_glb(path)
    inferred = rigged_avatar(path)
    assert inferred.scale == 0.01
    assert inferred.height_m == pytest.approx(H, abs=1e-6)
    assert any("reads as cm" in note for note in inferred.describe()["notes"])
    with pytest.raises(RigSkinError, match="180 m tall"):
        rigged_avatar(path, units="m")
