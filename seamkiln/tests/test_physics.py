"""True-to-life physics (A54 P0/P1), checked against a real standard.

The Cusick drape test (BS 5058 / ISO 9073-9) is the textile industry's ruler
for "does this cloth behave": a 300 mm circular specimen over a 180 mm disc,
and the drape coefficient is how much of its own shadow it keeps. Stiff cloth
scores near 1, limp cloth near 0. Running it here is what makes "true-to-life
physics" a measurement rather than an adjective - and it is what caught the
bending model being wrong in the first place.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.drape.body import (
    cusick_pedestal,
    place,
    sdf_from_mesh,
    solid_ball,
)
from seamkiln.drape.cusick import drape_coefficient, specimen
from seamkiln.drape.environment import (
    EARTH_G,
    GRAVITY_PRESETS,
    STANDARD_HUMIDITY,
    Environment,
    WindField,
)
from seamkiln.drape.garment import Placement, bending_quads, build_garment
from seamkiln.drape.solve import QUALITY, DrapeSettings, drape, vertex_areas
from seamkiln.pattern.fabric import fabric

# -- the room ----------------------------------------------------------------


def test_air_density_matches_the_textbook() -> None:
    """1.20 kg/m3 at the ISO 139 standard atmosphere. If this drifts, the wind
    force is wrong by the same factor and nothing downstream will say so."""
    assert Environment().air_density() == pytest.approx(1.197, abs=0.01)
    # cold dry air is DENSER; warm humid air is LIGHTER (water is lighter
    # than nitrogen), which surprises people and is worth pinning down
    assert Environment(temperature_c=-5, humidity=0.3).air_density() > 1.30
    assert Environment(temperature_c=35, humidity=0.9).air_density() < 1.13


def test_gravity_is_a_vector_and_can_point_anywhere() -> None:
    assert Environment().gravity_vector()[1] == pytest.approx(-EARTH_G)
    sideways = Environment(gravity_direction=(1.0, 0.0, 0.0))
    assert sideways.gravity_vector()[0] == pytest.approx(EARTH_G)
    assert Environment.preset("moon").gravity == pytest.approx(1.625)
    assert np.allclose(Environment.preset("zero").gravity_vector(), 0.0)
    with pytest.raises(ValueError, match="no gravity preset"):
        Environment.preset("pluto")
    assert set(GRAVITY_PRESETS) >= {"earth", "moon", "mars", "zero"}


def test_moisture_regain_is_the_published_constant_at_the_standard_atmosphere() -> None:
    room = Environment(humidity=STANDARD_HUMIDITY)
    assert room.regain("cotton") == pytest.approx(0.085, abs=0.001)
    assert room.regain("wool") == pytest.approx(0.160, abs=0.001)
    assert room.regain("polyester") < 0.01
    # bone-dry cloth holds no water and is stiffer for it
    dry = Environment(humidity=0.0).conditioning("cotton")
    assert dry["regain"] == pytest.approx(0.0)
    assert dry["mass_factor"] == pytest.approx(1.0)
    assert dry["compliance_factor"] < 1.0


def test_conditioning_says_which_half_is_measured() -> None:
    tiers = Environment().conditioning("cotton")["tier"]
    assert "measured" in tiers["regain_at_65"]
    assert "plausible" in tiers["softening"]


def test_a_gust_is_deterministic() -> None:
    """A drape that cannot repeat itself cannot be benchmarked, and 'it was
    windy' is not an excuse."""
    field = WindField.of(Environment(wind=(5.0, 0.0, 0.0), wind_gust=0.5))
    assert np.allclose(field.samples(50), field.samples(50))
    assert not np.allclose(field.at(0), field.at(37))
    steady = WindField.of(Environment(wind=(5.0, 0.0, 0.0)))
    assert np.allclose(steady.at(0), steady.at(999))


# -- the test subject --------------------------------------------------------


def test_the_ball_is_a_ball() -> None:
    ball = solid_ball(0.15)
    assert ball.volume == pytest.approx(4 / 3 * np.pi * 0.15**3, rel=0.01)
    assert ball.is_watertight
    with pytest.raises(ValueError, match="positive radius"):
        solid_ball(0.0)


def test_the_subject_can_be_moved_without_rebaking_its_field() -> None:
    """Rebuilding an SDF is ~1.5 s; a rotation is a 3x3 multiply. Moving the
    test subject has to be the cheap one or nobody will move it."""
    sdf = sdf_from_mesh(solid_ball(0.15), voxel_mm=6.0)
    assert sdf.placed is False
    assert sdf.sample(np.array([[0.0, 0.0, 0.0]]))[0] < -0.10

    moved = sdf.moved((0.5, 1.0, 0.0))
    assert moved.placed is True
    assert moved.grid is sdf.grid, "the field was rebuilt instead of moved"
    assert moved.sample(np.array([[0.5, 1.0, 0.0]]))[0] < -0.10
    assert moved.sample(np.array([[0.0, 0.0, 0.0]]))[0] > 0.5


def test_place_moves_turns_and_resizes() -> None:
    ball = solid_ball(0.1)
    moved = place(ball, (1.0, 2.0, 3.0), scale=2.0)
    assert np.allclose(moved.bounds.mean(axis=0), [1.0, 2.0, 3.0], atol=1e-6)
    assert moved.extents.max() == pytest.approx(0.4, rel=0.02)


# -- the physics that had to be rebuilt --------------------------------------


def test_bending_is_a_dihedral_quad_not_a_distance_pair() -> None:
    """A distance between opposite corners changes only QUADRATICALLY with
    the fold angle, so it resists a crease and ignores gentle curvature - and
    drape IS gentle curvature. Measured: a cloth with every compliance at
    1e-6, rigid by any reading, still collapsed to a drape coefficient of
    0.17 and fell 69 mm off a 300 mm disc."""
    triangles = np.array([[0, 1, 2], [0, 1, 3]], dtype=np.int32)
    quads = bending_quads(triangles)
    assert quads.shape == (1, 4)
    assert set(quads[0].tolist()) == {0, 1, 2, 3}


def test_a_flat_pattern_rests_at_pi_not_zero() -> None:
    """Both triangles are listed off the same shared edge, so a FLAT sheet has
    n1 . n2 = -1. Resting at zero told every element to fold itself in half,
    and the specimen contracted from a 150 mm radius to 8 mm."""
    pattern = specimen(200.0)
    garment = build_garment(pattern, {"SPECIMEN": Placement(flat=True)}, particle_distance=20.0)
    assert garment.bending.shape[1] == 4
    assert np.allclose(garment.bending_rest, np.pi)


def test_weight_is_per_particle_from_the_fabrics_own_gsm() -> None:
    """A uniform inverse mass is only right on a uniform mesh: where the mesh
    is fine, particles were too heavy; where it is coarse, too light."""
    pattern = specimen(200.0)
    garment = build_garment(pattern, {"SPECIMEN": Placement(flat=True)}, particle_distance=15.0)
    share = vertex_areas(garment.rest_points_mm, garment.triangles)
    assert share.sum() == pytest.approx(np.pi * 0.1**2, rel=0.05)  # the disc's area
    assert share.max() > share.min() * 1.2, "every particle got the same share"


def test_quality_tiers_change_the_physics_not_just_the_picture() -> None:
    """Bending converges over substeps, so a draft drape is not a rougher
    picture of the same cloth - it is SOFTER cloth. Measured on denim:
    DC 0.431 at 8 substeps, 0.876 at 20, 0.995 at 50."""
    assert QUALITY["draft"]["substeps"] < QUALITY["standard"]["substeps"]
    assert QUALITY["standard"]["substeps"] >= 20
    assert DrapeSettings.at_quality("fine").substeps > DrapeSettings().substeps
    with pytest.raises(ValueError, match="no quality"):
        DrapeSettings.at_quality("cinematic")


# -- the standard ------------------------------------------------------------


def test_a_flat_specimen_scores_one() -> None:
    """The calibration check: nothing has fallen, so the shadow is the whole
    specimen and the coefficient is 1."""
    from seamkiln.drape.triangulate import triangulate_panel

    mesh = triangulate_panel(specimen().panel("SPECIMEN"), particle_distance=10.0)
    flat = np.column_stack(
        [mesh.points[:, 0] * 1e-3, np.zeros(mesh.n_points), mesh.points[:, 1] * 1e-3]
    )
    result = drape_coefficient(flat, mesh.triangles)
    assert result.value == pytest.approx(1.0, abs=0.01)
    assert result.node_count == 0, "a flat disc has no folds"


@pytest.mark.slow
def test_the_bundled_fabrics_land_in_their_published_drape_bands() -> None:
    """The claim, as a test. Cotton jersey is the known exception and is
    listed: it is a knit, and the model was fitted on wovens."""
    from seamkiln.drape import cusick_run

    bands = {
        "denim_12oz": (0.75, 0.90),
        "wool_suiting": (0.55, 0.75),
        "cotton_poplin": (0.50, 0.70),
        "silk_habotai": (0.25, 0.40),
        "chiffon": (0.15, 0.30),
    }
    for name, (low, high) in bands.items():
        value = cusick_run.run(name, particle_distance=8.0, frames=300, substeps=20)[
            "drape_coefficient"
        ]
        assert low <= value <= high, f"{name} scored {value:.3f}, band {low}-{high}"


def test_gravity_and_wind_actually_move_the_cloth() -> None:
    """Cheap version of the room sweep: the moon must drape less than earth."""
    pattern = specimen()
    sdf = sdf_from_mesh(cusick_pedestal(0.18, 0.30), voxel_mm=6.0, pad_mm=140.0)
    flat = Placement(
        flat=True,
        origin_m=np.array([0.0, 0.306, 0.0]),
        rotation=np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]]),
    )
    folds = {}
    for label, room in (("earth", Environment()), ("moon", Environment.preset("moon"))):
        garment = build_garment(pattern, {"SPECIMEN": flat}, particle_distance=14.0)
        pins = (np.linalg.norm(garment.points[:, [0, 2]], axis=1) < 0.010).astype(float)
        result = drape(
            garment,
            sdf,
            fabric="cotton_poplin",
            pins=pins,
            settings=DrapeSettings(frames=120, substeps=12, environment=room),
        )
        folds[label] = float(result.points[:, 1].max() - result.points[:, 1].min())
    assert folds["moon"] < folds["earth"], "gravity did nothing"


def test_pins_hold() -> None:
    pattern = specimen(200.0)
    # HORIZONTAL, or there is nowhere to droop: `flat=True` with no rotation
    # lays the panel in the world XY plane, which is a vertical curtain, and a
    # vertical curtain pinned down its middle hangs rather than falls.
    horizontal = Placement(
        flat=True,
        origin_m=np.array([0.0, 1.0, 0.0]),
        rotation=np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]]),
    )
    garment = build_garment(pattern, {"SPECIMEN": horizontal}, particle_distance=15.0)
    sdf = sdf_from_mesh(solid_ball(0.02, (0.0, -5.0, 0.0)), voxel_mm=10.0)
    pinned = np.linalg.norm(garment.points[:, [0, 2]], axis=1) < 0.02
    before = garment.points[pinned].copy()
    result = drape(
        garment,
        sdf,
        fabric="chiffon",
        pins=pinned.astype(float),
        settings=DrapeSettings(frames=200, substeps=10),
    )
    assert np.allclose(result.points[pinned], before, atol=1e-9), "a pin let go"
    assert result.points[~pinned, 1].min() < before[:, 1].min() - 0.02, "nothing fell"


def test_the_report_stays_compact_when_the_room_is_ordinary() -> None:
    """Report the exception, not the default: spelling out an unchanged room
    in every drape pushed the response past its budget."""
    pattern = specimen(200.0)
    garment = build_garment(pattern, {"SPECIMEN": Placement(flat=True)}, particle_distance=20.0)
    sdf = sdf_from_mesh(solid_ball(0.05, (0.0, -1.0, 0.0)), voxel_mm=10.0)
    ordinary = drape(garment, sdf, settings=DrapeSettings(frames=10)).report()
    assert len(repr(ordinary)) < 800
    assert ordinary["room"] == "standard atmosphere"
    assert "gravity" not in ordinary and "wind_ms" not in ordinary

    garment2 = build_garment(pattern, {"SPECIMEN": Placement(flat=True)}, particle_distance=20.0)
    windy = drape(
        garment2,
        sdf,
        settings=DrapeSettings(
            frames=10, environment=Environment.preset("mars", wind=(4.0, 0.0, 0.0))
        ),
    ).report()
    assert windy["gravity"][1] == pytest.approx(-3.721)
    assert windy["wind_ms"] == [4.0, 0.0, 0.0]


def test_the_fabric_card_carries_rigidity_in_real_units() -> None:
    """Drape depends on stiffness RELATIVE TO WEIGHT. The old card had a
    dimensionless bend number, which meant weight did not affect drape at
    all - a 400 g/m2 denim and a 40 g/m2 chiffon of the same number draped
    identically, which is wrong about cloth."""
    denim = fabric("denim_12oz")
    chiffon = fabric("chiffon")
    assert denim.bend_warp > chiffon.bend_warp * 100  # mN.mm, real spread
    assert denim.compliances()["bending"] < chiffon.compliances()["bending"]
    jersey = fabric("cotton_jersey")
    assert jersey.gsm > fabric("cotton_poplin").gsm
    assert jersey.compliances()["bending"] > fabric("cotton_poplin").compliances()["bending"]


# -- never rely on a coarse preview ------------------------------------------


def test_a_drape_that_has_not_converged_says_so() -> None:
    """The rule, made structural. A draft run is not a rougher picture of the
    same cloth - it is softer cloth - so the result labels itself rather than
    depending on whoever reads it to remember."""
    from seamkiln.drape.body import mannequin
    from seamkiln.drape.garment import build_garment, top_arrangement
    from seamkiln.pattern.fixtures import tee_block

    body = mannequin()
    field = sdf_from_mesh(body, voxel_mm=8.0)
    pattern = tee_block()

    coarse = build_garment(pattern, top_arrangement(pattern, body), particle_distance=22.0)
    draft = drape(
        coarse,
        field,
        fabric="cotton_poplin",
        settings=DrapeSettings(frames=120, substeps=8),
    ).report()
    assert draft["converged"] is False
    assert any("substeps" in reason for reason in draft["not_converged"])


def test_a_mesh_too_coarse_for_its_own_seams_refuses() -> None:
    """A seam sampled too thinly cannot close, so the floor is a refusal
    rather than a warning - and it names the finer distance to use."""
    from seamkiln.drape.body import mannequin
    from seamkiln.drape.garment import MIN_SEAM_POINTS, build_garment, top_arrangement
    from seamkiln.pattern.fixtures import tee_block

    body = mannequin()
    pattern = tee_block()
    with pytest.raises(ValueError, match="too coarse for this garment's seams"):
        build_garment(pattern, top_arrangement(pattern, body), particle_distance=30.0)

    ok = build_garment(pattern, top_arrangement(pattern, body), particle_distance=16.0)
    assert min(ok.seam_points.values()) >= MIN_SEAM_POINTS


def test_the_back_panel_is_mirrored_when_worn() -> None:
    """You look at a back panel from BEHIND, so its pattern-right edge is the
    body's left. Sewing FRONT#1 to BACK#1 wraps the garment round the wearer:
    the left sleeve was joined to the right half of the back armhole, one
    point at x = -0.099 paired with one at x = +0.105, and that single seam
    accounted for a 211 mm gap. It looked like a resolution problem and was
    not - it was identical from 26 mm down to 9 mm, which is what a topology
    bug looks like and what a convergence problem does not."""
    import numpy as np

    from seamkiln.drape.body import mannequin, sdf_from_mesh
    from seamkiln.drape.garment import build_garment, top_arrangement
    from seamkiln.pattern.fixtures import tee_block

    body = mannequin()
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=16.0)
    result = drape(
        garment,
        sdf_from_mesh(body, voxel_mm=8.0),
        fabric="cotton_poplin",
        settings=DrapeSettings(frames=250),
    )
    # No sewn pair may straddle the body's centre line. A handful near the
    # centre front and centre back legitimately do, so the test is about the
    # ones far out on either side - those can only be a crossed seam.
    left = result.points[garment.seams[:, 0], 0]
    right = result.points[garment.seams[:, 1], 0]
    crossed = int((((left * right) < 0) & (np.abs(left) > 0.05) & (np.abs(right) > 0.05)).sum())
    assert crossed == 0, f"{crossed} sewn pairs straddle the body"
    assert result.seam_gaps["max_gap_mm"] < 90.0


def test_a_fit_report_refuses_to_quote_an_unconverged_drape() -> None:
    """ "Never rely on a coarse preview" is a rule about REPORTING, so the
    refusal lives where the numbers would be quoted."""
    from seamkiln.session import Command, CommandError, Session

    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    session.apply(Command("body", {"kind": "mannequin"}))
    session.apply(Command("arrange", {"particle_distance_mm": 22.0}))
    session.apply(Command("drape", {"fabric": "cotton_poplin", "frames": 60, "substeps": 8}))
    with pytest.raises(CommandError, match="not worth quoting"):
        session.apply(Command("fit", {}))
    # explicit override, because iterating is legitimate and lying is not
    allowed = session.apply(Command("fit", {"allow_unconverged": True}))
    assert allowed["converged"] is False
    assert allowed["not_converged"]
