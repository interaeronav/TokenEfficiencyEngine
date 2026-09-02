"""A figure that can be dressed, an arrangement the pattern dictates, and a
dressing step that keeps the garment on the body.

Every number here was measured on the figure and the mannequin at a particle
distance that converges for the claim being made.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from seamkiln.avatar import Pose, figure_factory, gait, rigid_factory, walk
from seamkiln.drape.body import mannequin, sdf_from_mesh
from seamkiln.drape.dressing import (
    BodyFrame,
    dress,
    frame_from_figure,
    frame_from_mesh,
    shoulder_anchors,
    shoulder_drop_mm,
    wrap_arrangement,
)
from seamkiln.drape.garment import build_garment
from seamkiln.drape.solve import DrapeSettings
from seamkiln.figure import PARTS, clasp_points, figure, joints, standing_offset
from seamkiln.pattern.fixtures import jacket_block, tee_block
from seamkiln.session import Command, CommandError, Session

H = 1.80
ARM_MM = 2.0 * math.pi * H * 0.034 * 1000.0


def coat_block():
    return jacket_block(
        opening="zipper",
        length=700.0,
        half_chest=420.0,
        shoulder=250.0,
        sleeve_length=480.0,
        cuff=170.0,
        biceps=ARM_MM * 1.25,
    )


# -- the figure ----------------------------------------------------------------


def test_the_figure_is_one_watertight_mesh_with_every_part_tagged() -> None:
    body = figure(Pose(), height=H)
    assert body.is_watertight
    assert sorted(set(body.metadata["part_per_face"].tolist())) == list(range(len(PARTS)))
    colours = np.asarray(body.visual.vertex_colors)
    assert sorted(set(colours[:, 0].tolist())) == [t * 40 + 20 for t in range(len(PARTS))]
    assert body.extents[1] == pytest.approx(1.874, abs=0.01)


def test_the_figure_faces_forward_and_turns_with_its_clasps() -> None:
    """Built facing +Z - the plane its joints swing in and what the cylinder
    arrangement calls 'front'. The first shot ran a whole sequence sideways
    because the figure faced Z while travelling X."""
    front = figure(Pose(), height=H)
    assert float(front.vertices[:, 2].max()) > 0.15, "the toes should point +Z"
    turned = figure(Pose(), height=H, facing_deg=90.0)
    assert float(turned.vertices[:, 0].max()) > 0.15, "turned 90, the toes point +X"
    left, right = clasp_points(Pose(), height=H)
    assert left[0] < 0 < right[0] and left[2] < 0, "clasps sit on the shoulders, behind"
    tl, _tr = clasp_points(Pose(), height=H, facing_deg=90.0)
    assert tl[0] == pytest.approx(left[2], abs=1e-9)  # the yaw carried them round


def test_the_figure_is_clothable_not_comic() -> None:
    """A 0.054H upper arm is 194 mm across on a 1.8 m body; a real one is
    about 100. No sleeve drafted to a matching armhole could go round it, and
    the sleeves flapped beside bare arms - which looked like a cloth bug and
    was an anatomy bug."""
    assert pytest.approx(122.4, abs=0.1) == 2 * H * 0.034 * 1000
    j = joints(Pose(), height=H)
    assert j["shoulder_l"][1] == pytest.approx(1.40, abs=0.02)
    off = standing_offset(figure(Pose(), height=H))
    assert off[1] > 0.0, "the lowest point is put ON the ground, never through it"


# -- the arrangement -----------------------------------------------------------


def test_a_wrap_arrangement_takes_its_radius_from_the_pattern() -> None:
    """The panels have a total width and must wrap the cylinder exactly once,
    so the radius is that width over 2*pi. Guessing it put a 1140 mm jacket on
    a 1847 mm cylinder and left 68 degrees of open arc on each side."""
    pattern = coat_block()
    frame = frame_from_figure(Pose(), height=H)
    placements = wrap_arrangement(pattern, frame, height=H)
    body = [p for p in pattern.panels if not p.id.startswith("SLEEVE")]
    total = sum(p.bbox[2] - p.bbox[0] for p in body) / 1000.0
    assert placements["BACK"].radius_m == pytest.approx(total / (2 * math.pi), rel=1e-6)
    # the two fronts sit side by side, not on top of each other
    assert placements["FRONT_R"].centre_angle_deg > 0 > placements["FRONT_L"].centre_angle_deg
    # a sleeve wraps ITS OWN width - guessed at twice that, the tube never closed
    sleeve = pattern.panel("SLEEVE_L")
    assert placements["SLEEVE_L"].radius_m == pytest.approx(
        (sleeve.bbox[2] - sleeve.bbox[0]) / 1000.0 / (2 * math.pi), rel=1e-6
    )


def test_the_collar_clears_the_shoulder_cap_by_derivation() -> None:
    """Start the top edge level with the joint and the deltoid caps poke out
    through the collar; the coat reads as slipped off when it has not moved.
    The clearance is derived from the cap and the pattern's own drop, not
    picked - a fixed fraction of stature was right for exactly one body."""
    pattern = coat_block()
    frame = frame_from_figure(Pose(), height=H)
    drop = shoulder_drop_mm(pattern)
    assert drop == pytest.approx(42.0, abs=1.0)
    top = float(frame.neck[1]) + frame.clearance(drop / 1000.0)
    assert top - drop / 1000.0 >= frame.shoulder_y + frame.cap_m - 1e-9


def test_a_sleeve_with_no_arm_to_hang_from_is_refused() -> None:
    frame = BodyFrame(shoulder_y=1.4, neck=np.array([0.0, 1.44, 0.0]), arms={})
    with pytest.raises(ValueError, match="no 'l' arm axis"):
        wrap_arrangement(tee_block(), frame)


def test_a_mesh_frame_anchors_its_neck_from_the_shoulder() -> None:
    """On the figure the landmark scan read the neck 140 mm high (the head-cowl
    junction, the narrowest slice in the top fifth) while the shoulder landed
    within 13 mm. The reliable one anchors the unreliable one."""
    body = figure(Pose(), height=H)
    body.apply_translation(standing_offset(body))
    measured = frame_from_mesh(body)
    known = frame_from_figure(Pose(), height=H)
    lift = standing_offset(figure(Pose(), height=H))[1]
    assert measured.shoulder_y == pytest.approx(known.shoulder_y + lift, abs=0.03)
    assert measured.neck[1] == pytest.approx(measured.shoulder_y + 0.02, abs=1e-9)
    assert set(measured.arms) == {"l", "r"}


# -- dressing ------------------------------------------------------------------


@pytest.fixture(scope="module")
def dressed_coat():
    body = figure(Pose(), height=H)
    off = standing_offset(body)
    body.apply_translation(off)
    pattern = coat_block()
    frame = frame_from_figure(Pose(), height=H)
    garment = build_garment(
        pattern, wrap_arrangement(pattern, frame, height=H), particle_distance=12.0
    )
    garment.points = garment.points + off
    result = dress(
        garment,
        sdf_from_mesh(body, voxel_mm=12.0),
        fabric="wool_suiting",
        anchors=shoulder_anchors(frame, off),
    )
    return body, frame, garment, result, off


def test_dressing_keeps_the_coat_on_the_body(dressed_coat) -> None:
    """The failure this exists for: a cylinder arrangement closes into a tube
    whose shoulders are on the wearer's flanks, and a tube with no shoulders
    slides straight off. Seams closed to 4.7 mm and the jacket ended at
    y = -0.79 on the floor, with `worn` correctly False."""
    _body, frame, _garment, result, off = dressed_coat
    assert result.contact["worn"] is True
    assert result.contact["touching_fraction"] > 0.15
    assert result.seam_gaps["mean_gap_mm"] < 4.0
    # on the shoulders: the top edge is at or above the shoulder joint
    assert float(result.points[:, 1].max()) > frame.shoulder_y + off[1]
    # and it is a coat, not a bolero: the hem reaches past the hip
    assert float(result.points[:, 1].min()) < joints(Pose(), height=H)["pelvis"][1] + off[1]


def test_dressing_pins_the_seam_whichever_way_its_indices_run() -> None:
    """Which end of a seam is the neck end is not knowable from the index order,
    so both are tried and the one that moves the cloth less wins - the same
    measured-not-declared choice the seam pairing makes about orientation.

    Measured at the end of the HOLD, against the line the pins actually use:
    the neck-to-shoulder line lifted onto the shoulder. What the coat does
    once let go is a fact about the coat (open at the front, light, slippery
    on smooth limbs, and it drifts) and is reported as `drift_mm`, not
    asserted here."""
    from seamkiln.drape.dressing import outside_the_body

    body = figure(Pose(), height=H)
    off = standing_offset(body)
    body.apply_translation(off)
    pattern = coat_block()
    frame = frame_from_figure(Pose(), height=H)
    garment = build_garment(
        pattern, wrap_arrangement(pattern, frame, height=H), particle_distance=12.0
    )
    garment.points = garment.points + off
    field = sdf_from_mesh(body, voxel_mm=12.0)
    anchors = shoulder_anchors(frame, off)
    result = dress(garment, field, fabric="wool_suiting", anchors=anchors, settle_frames=1)
    for seam_id, (start, end) in anchors.items():
        lo, hi = garment.seam_spans[seam_id]
        seam = result.points[garment.seams[lo:hi].reshape(-1)]
        line = start + (end - start) * np.linspace(0.0, 1.0, 9)[:, None]
        lifted, _ = outside_the_body(field, line, standoff_m=0.01, direction="up")
        assert float(np.linalg.norm(seam.mean(axis=0) - lifted.mean(axis=0))) < 0.06, seam_id
        assert float(seam[:, 1].mean()) > frame.shoulder_y + off[1], "on top of the shoulder"
    assert result.dressing["drift_mm"] < 60.0, "one settle frame relaxes the pins; no slide"


def test_a_missing_anchor_seam_is_named() -> None:
    body = mannequin()
    pattern = tee_block()
    frame = frame_from_mesh(body)
    garment = build_garment(pattern, wrap_arrangement(pattern, frame), particle_distance=25.0)
    with pytest.raises(ValueError, match="no seam\\(s\\) \\['collar'\\]"):
        dress(
            garment,
            sdf_from_mesh(body, voxel_mm=12.0),
            fabric="cotton_poplin",
            anchors={"collar": (np.zeros(3), np.ones(3))},
            hold_frames=2,
            settle_frames=2,
        )


# -- the session decides, and records the decision -----------------------------


def test_the_mannequin_keeps_the_cylinder_and_everything_else_gets_the_wrap() -> None:
    """Every number in this project's physics tests was produced by the
    cylinder arrangement on the mannequin, so the mannequin keeps it. Any other
    body gets the wrap - and the choice is RECORDED, so a replay makes it."""
    m = Session()
    m.apply(Command("block", {"block": "tee"}))
    m.apply(Command("body", {"kind": "mannequin"}))
    assert m.apply(Command("arrange", {"particle_distance_mm": 22.0}))["arrangement"] == "cylinder"

    f = Session()
    f.apply(Command("block", {"block": "tee", "half_chest": 300.0}))
    f.apply(Command("body", {"kind": "figure", "stature_m": H}))
    out = f.apply(Command("arrange", {"particle_distance_mm": 20.0, "dress": False}))
    assert out["arrangement"] == "wrap" and f.arrangement == "wrap"
    # an explicit override is honoured...
    forced = Session()
    forced.apply(Command("block", {"block": "tee"}))
    forced.apply(Command("body", {"kind": "mannequin"}))
    assert (
        forced.apply(
            Command(
                "arrange", {"particle_distance_mm": 22.0, "arrangement": "wrap", "dress": False}
            )
        )["arrangement"]
        == "wrap"
    )
    # ... and a spelling that is not a choice is refused
    with pytest.raises(CommandError, match="'auto', 'cylinder' or 'wrap'"):
        forced.apply(Command("arrange", {"arrangement": "cylindrical"}))


def test_a_figure_is_dressed_on_arrange_and_the_script_replays_it() -> None:
    s = Session()
    s.apply(
        Command(
            "block",
            {
                "block": "jacket-zip",
                "half_chest": 420.0,
                "shoulder": 250.0,
                "sleeve_length": 480.0,
                "cuff": 170.0,
                "biceps": 480.0,
            },
        )
    )
    s.apply(Command("body", {"kind": "figure", "stature_m": H}))
    out = s.apply(Command("arrange", {"particle_distance_mm": 12.0}))
    assert out["arrangement"] == "wrap" and out["dressed"] is True and out["worn"] is True
    assert out["touching_fraction"] > 0.15
    assert Session.replay(s.script()).fingerprint() == s.fingerprint()


def test_walk_uses_the_sessions_own_body() -> None:
    """It did not: the verb built a posed mannequin whatever body had been
    chosen, so 'walk' on a figure or an imported avatar animated something
    else entirely."""
    s = Session()
    s.apply(Command("block", {"block": "tee", "half_chest": 300.0}))
    s.apply(Command("body", {"kind": "figure", "stature_m": H}))
    s.apply(Command("arrange", {"particle_distance_mm": 18.0, "dress": False}))
    s.fabric = "cotton_jersey"
    out = s.apply(
        Command(
            "walk",
            {
                "gait": "walk",
                "cycles": 0.4,
                "fps": 12.0,
                "travel": True,
                "voxel_mm": 14.0,
                "substeps": 18,
            },
        )
    )
    assert out["body"] == "figure"
    assert out["worn_throughout"] is True
    # it TRAVELLED, at the gait's own speed - not a number picked to frame a shot
    assert out["travelled_m"] == pytest.approx(1.35 * out["duration_s"], rel=0.15)


def test_a_body_with_no_joints_walks_as_one_piece_and_says_so() -> None:
    body = mannequin()
    factory = rigid_factory(body)
    assert getattr(factory, "rigid", False) is True
    moved = factory({"rise_m": 0.05})
    assert float(moved.bounds[0][1]) == pytest.approx(float(body.bounds[0][1]) + 0.05, abs=1e-9)


def test_travel_moves_cloth_at_the_gaits_speed() -> None:
    pose = Pose()
    body = figure(pose, height=H)
    off = standing_offset(body)
    pattern = tee_block(half_chest=300.0)
    garment = build_garment(
        pattern,
        wrap_arrangement(pattern, frame_from_figure(pose, height=H), height=H),
        particle_distance=18.0,
    )
    garment.points = garment.points + off
    frames = walk(
        garment,
        gait("walk", cycles=0.4, samples_per_cycle=8),
        fabric="cotton_jersey",
        fps=12.0,
        voxel_mm=14.0,
        body_factory=figure_factory(height=H),
        settings=DrapeSettings(substeps=18),
        travel=True,
    )
    z = [float(f.points[:, 2].mean()) for f in frames]
    speed = (z[-1] - z[0]) / max(frames[-1].time_s, 1e-9)
    assert speed == pytest.approx(1.35, rel=0.15), f"cloth travelled at {speed:.2f} m/s"
    assert all(f.report["contact"]["worn"] for f in frames)


# -- the armhole cap over the deltoid (A65 follow-up) ---------------------------


def test_a_sleeve_hangs_with_its_cap_toward_the_top_of_the_shoulder() -> None:
    """A minimal rotation onto the arm left the roll about the arm unset and
    put the cap apex at the FRONT of the arm; sewn to an armhole whose corner
    is on top of the shoulder, the sleeve had to twist a quarter turn and the
    twist piled up at the corner (95-150 mm open on both front armholes)."""
    from seamkiln.drape.dressing import _front_edge_side, _sleeve_frame

    pattern = coat_block()
    frame = frame_from_figure(Pose(), height=H)
    dets = []
    for tag in ("l", "r"):
        side = _front_edge_side(pattern, f"SLEEVE_{tag.upper()}")
        assert side in (1, -1), "the block declares which sleeve edge meets the front"
        _, direction = frame.arms[tag]
        rotation = _sleeve_frame(direction, side)
        dets.append(float(np.linalg.det(rotation)))
        assert np.allclose(rotation @ rotation.T, np.eye(3), atol=1e-9), "orthonormal"
        assert np.allclose(rotation @ np.asarray([0.0, -1.0, 0.0]), direction, atol=1e-9)
        apex = rotation @ np.asarray([0.0, 0.0, 1.0])
        assert abs(float(apex @ direction)) < 1e-9, "the apex direction is across the arm"
        assert apex[1] > 0.5, f"the cap apex should face up over the shoulder, got {apex}"
        front = rotation @ np.asarray([float(side), 0.0, 0.0])
        assert front[2] > 0.5, f"the front edge of the {tag} sleeve must face +Z, got {front}"
    # one piece for both arms means one of them is laid face-down
    assert sorted(round(d) for d in dets) == [-1, 1], dets
    assert _front_edge_side(tee_block(), "SLEEVE_L") in (1, -1, None)


def test_the_cap_starts_above_the_deltoid() -> None:
    pattern = coat_block()
    frame = frame_from_figure(Pose(), height=H)
    placements = wrap_arrangement(pattern, frame, height=H)
    sleeve = next(p for p in pattern.panels if p.id.startswith("SLEEVE"))
    assert placements[sleeve.id].top_y_m == pytest.approx(max(sleeve.bbox[3], 0.0) / 1000.0)
    assert placements[sleeve.id].top_y_m > 0.05, (
        "a cap that starts at the ball's equator ends under it"
    )


def test_targets_are_pinned_to_the_surface_never_to_the_bone() -> None:
    """Pin targets inside the body are instructions the solver cannot follow:
    collision decides which side each particle leaves on, and a seam pair can
    leave on two sides of a limb. Shoulder lines are lifted onto the shoulder;
    a lift that would go up through the head (the neck is a column, not a
    shelf) falls back to the gradient and lands on the neck's surface."""
    from seamkiln.drape.dressing import outside_the_body

    body = figure(Pose(), height=H)
    off = standing_offset(body)
    body.apply_translation(off)
    field = sdf_from_mesh(body, voxel_mm=12.0)
    j = joints(Pose(), height=H)
    neck, tip = j["neck"] + off, j["shoulder_r"] + off
    line = neck + (tip - neck) * np.linspace(0.0, 1.0, 9)[:, None]
    assert (field.sample(line) < 0).all(), "the neck-to-shoulder line runs inside the body"

    lifted, report = outside_the_body(field, line, standoff_m=0.01, direction="up")
    assert (field.sample(lifted) >= 0.0095).all()
    assert report["moved"] == 9
    shift = np.linalg.norm(lifted - line, axis=1)
    assert shift.max() < 0.15, f"a point went up through the head: {shift.max():.3f} m"
    assert report["fell_back_to_gradient"] >= 1, "the neck end should have gone by the gradient"
    assert lifted[-1][1] > tip[1] + 0.05, "the shoulder end sits on top of the deltoid"

    outside = line + np.asarray([0.0, 0.5, 0.0])
    same, untouched = outside_the_body(field, outside, standoff_m=0.01)
    assert np.allclose(same, outside) and untouched["moved"] == 0


def test_dressing_closes_the_armholes_over_the_deltoid(dressed_coat) -> None:
    """The regression this whole section exists for: measured at 109 mm on the
    fur jacket and 120 mm after the first fix, with the pairs straddling the
    ball. Now the cap sits over the shoulder and the worst pair is a seam
    allowance, not a limb."""
    _, _, garment, result, _ = dressed_coat
    from seamkiln.drape.tearing import seam_tension

    gaps = seam_tension(garment, result.points)
    worst = {k: v["max_gap_mm"] for k, v in gaps.items()}
    assert max(worst.values()) < 45.0, worst
    assert result.seam_gaps["mean_gap_mm"] < 4.0
    assert result.dressing["anchors_by_gradient"] >= 1
    assert result.dressing["shallowest_after_mm"] > 5.0
