"""The drape kernel (A53 P2): triangulation, body SDF, arrangement, solve.

Deliberately coarse and short - big meshes and long settles belong in the
bench, not the suite. What is asserted here is behaviour that a refactor
could silently break: that the mesh conforms to the panel, that the body
measures back the number it was built with, that seams find their own
orientation, that a drape does not enter the body AND does not fall off it,
and that the same input gives the same result twice.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pytest

from seamkiln.drape.body import mannequin, measure_contact, measure_penetration, sdf_from_mesh
from seamkiln.drape.garment import (
    arm_axes,
    body_landmarks,
    build_garment,
    edge_t_ranges,
    top_arrangement,
)
from seamkiln.drape.solve import DrapeSettings, anisotropic_compliance, drape
from seamkiln.drape.triangulate import resample_closed, triangulate_panel
from seamkiln.pattern.fabric import fabric
from seamkiln.pattern.fixtures import tee_block
from seamkiln.pattern.geometry import Vertex
from seamkiln.pattern.model import InternalLine, LineKind, Panel

# 25 mm keeps the suite fast while staying inside what the kernel can
# actually drape. MEASURED: at 40 mm the tee slides off (contact 0.07),
# because a 113 mm shoulder seam gets three points and three points do not
# hold a garment up. `triangulate_panel` now refuses that outright.
COARSE = 25.0


@pytest.fixture(scope="module")
def body():
    return mannequin()


@pytest.fixture(scope="module")
def sdf(body):
    return sdf_from_mesh(body, voxel_mm=12.0)


# -- triangulation -----------------------------------------------------------


def test_mesh_covers_the_panel_and_no_more() -> None:
    panel = tee_block().panel("FRONT")
    mesh = triangulate_panel(panel, particle_distance=20.0)
    p = mesh.points
    a, b, c = p[mesh.triangles[:, 0]], p[mesh.triangles[:, 1]], p[mesh.triangles[:, 2]]
    total = (
        0.5
        * np.abs(
            (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
        ).sum()
    )
    assert total == pytest.approx(panel.area_mm2, rel=0.02)


def test_a_cutout_becomes_a_hole_not_a_covered_patch() -> None:
    panel = Panel(
        id="P",
        outline=[Vertex(0, 0), Vertex(200, 0), Vertex(200, 200), Vertex(0, 200)],
        internals=[
            InternalLine(
                LineKind.CUTOUT,
                [Vertex(60, 60), Vertex(140, 60), Vertex(140, 140), Vertex(60, 140)],
                closed=True,
            )
        ],
    )
    mesh = triangulate_panel(panel, particle_distance=12.0)
    p = mesh.points
    a, b, c = p[mesh.triangles[:, 0]], p[mesh.triangles[:, 1]], p[mesh.triangles[:, 2]]
    total = (
        0.5
        * np.abs(
            (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
        ).sum()
    )
    assert total == pytest.approx(200 * 200 - 80 * 80, rel=0.05)


def test_particle_distance_is_the_knob_it_claims_to_be() -> None:
    panel = tee_block().panel("FRONT")
    coarse = triangulate_panel(panel, particle_distance=40.0)
    fine = triangulate_panel(panel, particle_distance=20.0)
    assert fine.n_points > coarse.n_points * 2.0
    assert fine.quality()["max_edge_mm"] < coarse.quality()["max_edge_mm"]


def test_relaxation_improves_the_worst_triangle() -> None:
    panel = tee_block().panel("FRONT")
    rough = triangulate_panel(panel, particle_distance=10.0, relax_passes=0).quality()
    smooth = triangulate_panel(panel, particle_distance=10.0, relax_passes=3).quality()
    assert smooth["min_angle_deg"] > rough["min_angle_deg"]


def test_resampling_keeps_every_original_vertex() -> None:
    outline = [Vertex(0, 0), Vertex(300, 0), Vertex(300, 100), Vertex(0, 100)]
    points, params = resample_closed(outline, 25.0)
    for vertex in outline:
        assert np.abs(points - np.array([vertex.x, vertex.y])).sum(axis=1).min() < 1e-9
    assert params.min() >= 0.0 and params.max() <= 1.0


def test_a_particle_distance_too_coarse_for_the_piece_refuses() -> None:
    """Not a cosmetic guard. At 40 mm the tee's shoulder seam gets three
    points, which cannot hold the garment up, and the drape slides off with
    every other number still looking healthy."""
    panel = tee_block().panel("FRONT")
    with pytest.raises(ValueError, match="too coarse"):
        triangulate_panel(panel, particle_distance=200.0)
    with pytest.raises(ValueError, match="particle_distance must be > 0"):
        triangulate_panel(panel, particle_distance=0.0)


# -- the body ----------------------------------------------------------------


def test_the_body_measures_back_the_chest_it_was_built_with(body) -> None:
    """A landmark routine that cannot recover a known input is not measuring."""
    marks = body_landmarks(body)
    assert marks["chest_girth_m"] == pytest.approx(1.00, rel=0.02)


def test_hips_wider_than_the_chest_do_not_become_the_chest() -> None:
    """The mannequin's hips ARE wider than its chest, as a real body's often
    are. Finding the chest as 'widest slice in the upper half' picked the
    hips and sized every garment to the wrong number."""
    marks = body_landmarks(mannequin(chest=0.9))
    assert marks["chest_girth_m"] == pytest.approx(0.9, rel=0.03)
    assert marks["chest_y_m"] < marks["shoulder_y_m"]


def test_arms_are_measured_not_assumed(body) -> None:
    marks = body_landmarks(body)
    arms = arm_axes(body, marks["chest_radius_m"])
    assert set(arms) == {"L", "R"}
    for side, arm in arms.items():
        direction = np.asarray(arm["direction"])
        assert direction[1] < -0.5, f"the {side} arm should point DOWNWARD"
        assert np.sign(direction[0]) == (-1 if side == "L" else 1)
        # built at 35 degrees from vertical; recovered from the mesh
        assert abs(direction[1]) == pytest.approx(np.cos(np.radians(35)), abs=0.05)


def test_sdf_signs_are_the_right_way_round(body, sdf) -> None:
    inside = np.array([[0.0, 1.1, 0.0]])
    far = np.array([[0.0, 1.1, 3.0]])
    assert sdf.sample(inside)[0] < 0.0
    assert sdf.sample(far)[0] > 1.0
    assert sdf.summary()["voxel_mm"] == 12.0


def test_contact_and_penetration_are_different_questions(sdf) -> None:
    """Both metrics exist because a garment on the floor scores a PERFECT
    zero for penetration - which is exactly what happened here once."""
    on_the_floor = np.zeros((50, 3))
    on_the_floor[:, 1] = -3.0
    assert measure_penetration(on_the_floor, sdf)["penetrating_points"] == 0
    assert measure_contact(on_the_floor, sdf)["worn"] is False


# -- arrangement -------------------------------------------------------------


def test_edge_spans_tile_the_whole_outline() -> None:
    ranges = edge_t_ranges(tee_block().panel("FRONT"))
    assert ranges[0][0] == pytest.approx(0.0)
    assert ranges[-1][1] == pytest.approx(1.0)
    for (_, end), (start, _) in pairwise(ranges):
        assert end == pytest.approx(start)


def test_every_panel_must_be_arranged(body) -> None:
    pattern = tee_block()
    placements = top_arrangement(pattern, body)
    placements.pop("SLEEVE_L")
    with pytest.raises(KeyError, match="SLEEVE_L"):
        build_garment(pattern, placements, particle_distance=COARSE)


def test_roles_name_the_pieces_when_the_ids_do_not(body) -> None:
    """A pattern from CAD is named by its maker - Frente, Costas, Manga - so
    the caller says which piece is which, and the arrangement is the one the
    block gets from its own ids. A wrong or unknown role refuses by name."""
    from dataclasses import replace

    from seamkiln.pattern.model import EdgeRef, Pattern, Seam

    original = tee_block()
    renamed = {
        "FRONT": "Frente",
        "BACK": "Costas",
        "SLEEVE_L": "Manga Esq",
        "SLEEVE_R": "Manga Dir",
    }
    pattern = Pattern(
        name="camiseta",
        panels=[replace(panel, id=renamed[panel.id]) for panel in original.panels],
        seams=[
            Seam(
                EdgeRef(renamed[s.a.panel], s.a.edge, s.a.t0, s.a.t1),
                EdgeRef(renamed[s.b.panel], s.b.edge, s.b.t0, s.b.t1),
                gather=s.gather,
                id=s.id,
            )
            for s in original.seams
        ],
        units="mm",
    )
    roles = {"Frente": "front", "Costas": "back", "Manga Esq": "sleeve_l", "Manga Dir": "sleeve_r"}
    expected = top_arrangement(original, body)
    got = top_arrangement(pattern, body, roles=roles)
    for old, new in renamed.items():
        assert np.allclose(got[new].rotation, expected[old].rotation)
        assert np.allclose(got[new].origin_m, expected[old].origin_m)
        assert got[new].centre_angle_deg == expected[old].centre_angle_deg
    # without roles the Portuguese ids all read as body pieces hung behind
    assert top_arrangement(pattern, body)["Frente"].centre_angle_deg == 180.0
    with pytest.raises(ValueError, match="does not have"):
        top_arrangement(pattern, body, roles={"FRONT": "front"})
    with pytest.raises(ValueError, match="must be one of"):
        top_arrangement(pattern, body, roles={"Frente": "collar"})


def test_rest_lengths_come_from_the_pattern_not_the_arrangement(body) -> None:
    """The property that makes this a garment and not a shrink-wrap."""
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=COARSE)
    flat = (
        np.linalg.norm(
            garment.rest_points_mm[garment.structural[:, 0]]
            - garment.rest_points_mm[garment.structural[:, 1]],
            axis=1,
        )
        * 1e-3
    )
    assert np.allclose(garment.structural_rest, flat)
    placed = np.linalg.norm(
        garment.points[garment.structural[:, 0]] - garment.points[garment.structural[:, 1]],
        axis=1,
    )
    assert not np.allclose(garment.structural_rest, placed), (
        "rest lengths match the ARRANGEMENT - the pattern has stopped mattering"
    )


def test_seams_choose_their_own_orientation(body) -> None:
    """Two counter-clockwise panels traverse a shared edge in opposite
    directions, so most seams need flipping. Getting it wrong twists the
    garment 180 degrees and reports nothing."""
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=COARSE)
    assert len(garment.seam_orientation) == 10
    assert any(v == "flipped" for v in garment.seam_orientation.values())
    assert any(v == "direct" for v in garment.seam_orientation.values())


def test_seam_pairs_are_in_register_and_the_two_sides_mirror(body) -> None:
    """Two runs of the same length sampled the same way differ in parameter
    by rounding only, and a first-at-or-after match turned that rounding into
    a one-vertex register error along a whole seam - on the tee, the right
    side seam and not the left, with the doubled pair at the armpit corner
    where three seams meet. That was an 82 mm open corner on the mannequin
    and the jacket's 0.7 mm convergence margin. Pairs are matched to the
    NEAREST vertex now, so a pair's two ends sit at the same height along a
    side seam and the left table is the right table's mirror image."""
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=12.0)
    rest = garment.rest_points_mm
    tables = {}
    for side in ("side-right", "side-left"):
        low, high = garment.seam_spans[side]
        pairs = garment.seams[low:high]
        ya, yb = rest[pairs[:, 0], 1], rest[pairs[:, 1], 1]
        above_hem = np.minimum(ya, yb) > 20.0  # the hem's loop-closing vertex is a known one-off
        assert np.abs(ya - yb)[above_hem].max() < 1e-6, f"{side} is out of register"
        top = pairs[np.argmax(np.maximum(ya, yb))]
        assert rest[top[0], 1] == rest[top[1], 1] == 420.0, (
            f"{side}: the corner pair is not corner to corner"
        )
        tables[side] = sorted(zip(np.round(ya, 6), np.round(yb, 6), strict=True))
    assert tables["side-right"] == tables["side-left"]


def test_the_garment_starts_as_one_mesh_with_every_panel_in_it(body) -> None:
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=COARSE)
    assert set(garment.panel_slices) == {"FRONT", "BACK", "SLEEVE_L", "SLEEVE_R"}
    assert garment.seams.shape[0] > 50
    assert garment.bending.shape[0] > 0
    total = sum(hi - lo for lo, hi in garment.panel_slices.values())
    assert total == garment.n_points


# -- the solve ---------------------------------------------------------------


def test_anisotropy_makes_the_bias_behave_differently() -> None:
    """Without this a bias-cut garment hangs exactly like a straight-grain
    one and the fabric card is decoration."""
    rest = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0]])
    pairs = np.array([[0, 1], [0, 2], [0, 3]], dtype=np.int32)  # weft, warp, bias
    values = anisotropic_compliance(rest, pairs, fabric("cotton_jersey"), 90.0)
    assert values[0] != pytest.approx(values[1]), "warp and weft behave identically"
    assert values[2] > min(values[0], values[1]), "the bias should not be the stiffest"


@pytest.mark.parametrize("cloth", ["cotton_jersey", "denim_12oz"])
def test_a_drape_stays_on_the_body_and_out_of_it(body, sdf, cloth) -> None:
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=COARSE)
    before = garment.seam_gaps_mm()
    result = drape(garment, sdf, fabric=cloth, settings=DrapeSettings(frames=120))

    assert result.seam_gaps["mean_gap_mm"] < before["mean_gap_mm"] / 20, "the seams did not close"
    assert result.contact["worn"] is True, "the garment came off the body"
    assert result.penetration["deepest_penetration_mm"] < 25.0, "cloth went through the body"
    assert np.isfinite(result.points).all()


def test_a_drape_reproduces_itself(body, sdf) -> None:
    pattern = tee_block()
    prints = set()
    for _ in range(2):
        garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=COARSE)
        prints.add(drape(garment, sdf, settings=DrapeSettings(frames=40)).fingerprint)
    assert len(prints) == 1


def test_the_report_is_compact_and_holds_no_vertices(body, sdf) -> None:
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=COARSE)
    report = drape(garment, sdf, settings=DrapeSettings(frames=20)).report()
    assert set(report) >= {"fabric", "seam_gaps", "penetration", "contact", "fingerprint"}
    assert len(repr(report)) < 800
