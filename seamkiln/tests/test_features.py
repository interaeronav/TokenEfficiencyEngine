"""A54 features: grading, cutting, tearing, pinching, lacing, finishing,
materials and blend-shape animation.

Every one of these is a garment operation with an arithmetic answer, so the
tests check the arithmetic rather than that the call returned. A dart of
width w and depth d removes exactly w*d/2 of cloth; a knife pleat of depth d
narrows a panel by exactly 2d; a lace at tension t closes an opening by t.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.animation import BlendTrack, Keyframe, animate, animation_report
from seamkiln.drape.body import mannequin, sdf_from_mesh
from seamkiln.drape.garment import build_garment, top_arrangement
from seamkiln.drape.pinching import Pinch, pinch, pinch_report
from seamkiln.drape.solve import DrapeSettings, drape
from seamkiln.drape.tearing import auto_rip, fray, rip_seam, seam_tension
from seamkiln.pattern import cutting
from seamkiln.pattern.fabric import Fabric, Tier, fabric
from seamkiln.pattern.fixtures import tee_block
from seamkiln.pattern.grading import (
    GradingError,
    Measurements,
    grade_to_measurements,
    size_run,
)

COARSE = 22.0


@pytest.fixture(scope="module")
def body():
    return mannequin()


@pytest.fixture(scope="module")
def sdf(body):
    return sdf_from_mesh(body, voxel_mm=12.0)


def draped(body, sdf, fabric_name="cotton_poplin", frames=150, pd=COARSE):
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=pd)
    return garment, drape(garment, sdf, fabric=fabric_name, settings=DrapeSettings(frames=frames))


# -- grading -----------------------------------------------------------------


def test_grading_scales_area_by_both_axes() -> None:
    pattern = tee_block()
    base = Measurements()
    target = Measurements(**{k: v * 1.10 for k, v in base.as_dict().items()})
    graded, report = grade_to_measurements(pattern, base, target)
    assert report.x_scale == pytest.approx(1.10)
    for before, after in zip(pattern.panels, graded.panels, strict=False):
        assert after.area_mm2 / before.area_mm2 == pytest.approx(1.10 * 1.10, rel=0.02)


def test_a_grade_too_far_from_the_block_refuses() -> None:
    """A proportional grade fits a body shaped like the block. Two sizes
    either side is normal practice; past that a pattern maker re-drafts."""
    base = Measurements()
    with pytest.raises(GradingError, match="outside the sane band"):
        grade_to_measurements(tee_block(), base, Measurements(chest=base.chest * 1.6))
    _, report = grade_to_measurements(
        tee_block(), base, Measurements(chest=base.chest * 1.6), strict=False
    )
    assert report.warnings


def test_measurements_come_off_a_real_body(body) -> None:
    measured = Measurements.from_body(body)
    assert measured.chest == pytest.approx(1000.0, rel=0.02)
    assert 380 < measured.back_length < 520  # a torso, not a leg
    assert 0.28 * measured.chest < measured.neck < 0.45 * measured.chest


def test_a_size_run_brackets_the_block() -> None:
    run = size_run(tee_block(), Measurements(), steps=2)
    assert list(run) == ["-2", "-1", "base", "+1", "+2"]
    areas = [run[k].total_area_mm2 for k in ("-2", "-1", "base", "+1", "+2")]
    assert areas == sorted(areas), "the run is not monotonic in size"


# -- cutting -----------------------------------------------------------------


def test_a_dart_removes_exactly_its_wedge() -> None:
    panel = tee_block().panel("FRONT")
    darted = cutting.dart(panel, (0.0, 400.0), (0.0, 0.0), 60.0)
    removed = panel.area_mm2 - darted.area_mm2
    assert removed == pytest.approx(0.5 * 60.0 * 400.0, rel=0.02)
    assert len(darted.internals) == len(panel.internals) + 1


def test_a_knife_pleat_takes_twice_its_depth() -> None:
    """The arithmetic people get wrong drafting one by hand: a pleat folds
    back on itself, so a knife pleat costs 2x its depth and a box pleat 4x."""
    panel = tee_block().panel("FRONT")
    width = panel.bbox[2] - panel.bbox[0]
    knife = cutting.pleat(panel, 0.0, 30.0, kind="knife")
    assert (knife.bbox[2] - knife.bbox[0]) == pytest.approx(width - 60.0, abs=1.0)
    box = cutting.pleat(panel, 0.0, 30.0, kind="box")
    assert (box.bbox[2] - box.bbox[0]) == pytest.approx(width - 120.0, abs=1.0)


def test_slash_and_spread_adds_fullness() -> None:
    panel = tee_block().panel("FRONT")
    spread = cutting.slash_spread(panel, (0.0, 600.0), (0.0, 0.0), 12.0)
    assert spread.area_mm2 > panel.area_mm2


def test_a_cut_that_misses_grazes_or_shatters_refuses() -> None:
    panel = tee_block().panel("FRONT")
    with pytest.raises(cutting.CuttingError, match="misses panel"):
        cutting.cut(panel, (2000, 2000), (2100, 2100))
    with pytest.raises(cutting.CuttingError, match="grazes"):
        cutting.cut(panel, (-300, 0), (300, 0))
    with pytest.raises(cutting.CuttingError, match="Reduce the depth"):
        cutting.pleat(panel, 0.0, 300.0, kind="box")


def test_a_cut_makes_two_pieces_that_add_up() -> None:
    panel = tee_block().panel("FRONT")
    result = cutting.cut(panel, (-300, 300), (300, 300))
    assert len(result.pieces) == 2
    total = sum(p.area_mm2 for p in result.pieces)
    assert total == pytest.approx(panel.area_mm2, rel=0.01)


# -- tearing -----------------------------------------------------------------


def test_ripping_a_seam_releases_its_constraints(body, sdf) -> None:
    garment, _ = draped(body, sdf)
    before = garment.seams.shape[0]
    torn, tear = rip_seam(garment, "side-right", fraction=0.5)
    assert tear.constraints > 0
    assert torn.seams.shape[0] == before - tear.constraints
    # the spans must still tile the new array, or a later rip cuts the wrong seam
    assert max(end for _, end in torn.seam_spans.values()) == torn.seams.shape[0]


def test_ripping_an_unknown_seam_lists_the_real_ones(body, sdf) -> None:
    garment, _ = draped(body, sdf)
    with pytest.raises(KeyError, match="side-right"):
        rip_seam(garment, "collar")


def test_the_load_picks_the_seam(body, sdf) -> None:
    """'Rips naturally along its seams' means nobody chooses the seam."""
    garment, result = draped(body, sdf, "denim_12oz")
    tension = seam_tension(garment, result.points)
    assert tension, "no seam reported a tension"
    weakest = max(tension, key=lambda k: tension[k]["max_gap_mm"])
    _, tears = auto_rip(garment, result.points, strength_mm=5.0)
    assert tears, "nothing tore at a 5 mm strength"
    assert weakest in {t.seam_id for t in tears}


def test_a_tear_frays(body, sdf) -> None:
    garment, result = draped(body, sdf)
    torn, tear = rip_seam(garment, "side-right", fraction=0.8)
    threads = fray(torn, result.points, [tear], length_mm=8.0, threads_per_vertex=3)
    assert threads.summary()["threads"] > 0
    assert 3.0 < threads.summary()["mean_length_mm"] < 13.0
    # deterministic: a frayed edge that changes every run cannot be rendered twice
    again = fray(torn, result.points, [tear], length_mm=8.0, threads_per_vertex=3)
    assert np.allclose(threads.ends, again.ends)


# -- pinching ----------------------------------------------------------------


def test_a_pinch_is_symmetric_and_holds(body, sdf) -> None:
    """Pinching one side and then the other is NOT the same as pinching both
    at once - the first grab has already dragged the cloth."""
    garment, result = draped(body, sdf)
    hem = result.points[result.points[:, 1] < np.percentile(result.points[:, 1], 10)]
    right = hem[np.argmax(hem[:, 0])]
    grabs = [Pinch(tuple(right), 55.0, tuple(right + np.array([0.15, 0.12, 0.05])))]

    pinches = pinch(garment, result.points, grabs, mirror=True)
    assert len(pinches.grabbed) == 2, "the mirror grab was not created"
    assert all(count > 0 for count in pinches.grabbed.values())

    garment.points = result.points.copy()
    after = drape(
        garment,
        sdf,
        pins=pinches.mask,
        pin_target=pinches.target,
        settings=DrapeSettings(frames=120),
    )
    report = pinch_report(result.points, after.points, pinches)
    assert report["symmetric"] is True
    assert report["held_moved_mm"] > 50.0, "the pinch did not pull"
    assert report["cloth_moved_mm"] > 5.0, "the cloth around it did not follow"


def test_a_pinch_that_reaches_nothing_grabs_nothing(body, sdf) -> None:
    garment, result = draped(body, sdf)
    pinches = pinch(garment, result.points, [Pinch((9.0, 9.0, 9.0), 10.0)], mirror=False)
    assert int(pinches.mask.sum()) == 0


# -- lacing ------------------------------------------------------------------


def test_a_lace_closes_the_opening_by_its_tension(body, sdf) -> None:
    from seamkiln.drape import lacing

    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=18.0)
    for seam in ("side-right", "side-left"):
        garment, _ = rip_seam(garment, seam, fraction=1.0)
    opened = drape(garment, sdf, fabric="cotton_poplin", settings=DrapeSettings(frames=150))

    left = lacing.eyelets_along(garment, opened.points, panel="FRONT", count=6)
    right = lacing.eyelets_along(garment, opened.points, panel="BACK", count=6)
    assert len(left) >= 2 and len(right) >= 2

    lace = lacing.thread(left, right, opened.points, style="criss-cross", tension=0.5)
    assert lace.meta["drawn_to_mm"] == pytest.approx(lace.meta["opening_mm"] * 0.5, rel=0.01)

    garment.points = opened.points.copy()
    lacing.apply(garment, lace)
    laced = drape(garment, sdf, fabric="cotton_poplin", settings=DrapeSettings(frames=200))
    before = np.linalg.norm(
        opened.points[lace.spans[:, 0]] - opened.points[lace.spans[:, 1]], axis=1
    ).mean()
    after = np.linalg.norm(
        laced.points[lace.spans[:, 0]] - laced.points[lace.spans[:, 1]], axis=1
    ).mean()
    assert after < before * 0.8, "the lace did not pull the opening in"


def test_lace_styles_and_refusals(body, sdf) -> None:
    from seamkiln.drape import lacing

    garment, result = draped(body, sdf)
    left = lacing.eyelets_along(garment, result.points, panel="FRONT", count=5)
    right = lacing.eyelets_along(garment, result.points, panel="BACK", count=5)
    for style in lacing.STYLES:
        assert lacing.thread(left, right, result.points, style=style).spans.shape[0] > 0
    with pytest.raises(ValueError, match="no lace style"):
        lacing.thread(left, right, result.points, style="bootlace")
    with pytest.raises(ValueError, match="tension runs 0"):
        lacing.thread(left, right, result.points, tension=2.0)
    with pytest.raises(KeyError, match="no panel"):
        lacing.eyelets_along(garment, result.points, panel="COLLAR")


# -- finishing ---------------------------------------------------------------


def test_a_wash_lifts_the_ground_and_hits_the_creases(body, sdf) -> None:
    from seamkiln import finishing

    garment, result = draped(body, sdf, "denim_12oz")
    raw = finishing.denim_wash(result.points, garment.triangles, level="raw")
    bleached = finishing.denim_wash(result.points, garment.triangles, level="bleached")
    assert bleached["colours"].mean() > raw["colours"].mean() + 0.2
    # raw is flat indigo; a wash has contrast because the creases are hit.
    # Compare SPATIAL variation per channel: the std of the whole array mixes
    # in the spread BETWEEN channels, and indigo's channels are far apart
    # while a bleached grey's are close, which reverses the comparison.
    assert raw["colours"].std(axis=0).max() == pytest.approx(0.0, abs=1e-9)
    assert bleached["colours"].std(axis=0).max() > 0.01
    assert raw["summary"]["p95_wear"] > 0.0
    with pytest.raises(ValueError, match="no wash level"):
        finishing.denim_wash(result.points, garment.triangles, level="acid")


def test_wear_follows_outward_folds_not_inward_ones(body, sdf) -> None:
    """Real abrasion happens where cloth bulges out and rubs; an inward fold
    is shielded, which is why the two look different on a pair of jeans."""
    from seamkiln.finishing import wear_field

    garment, result = draped(body, sdf, "denim_12oz")
    field = wear_field(result.points, garment.triangles)
    outward = field.curvature > 0
    assert field.wear[outward].mean() > field.wear[~outward].mean()


def test_fur_is_uniform_per_square_centimetre_and_fast(body, sdf) -> None:
    """Scattering per TRIANGLE grows a pelt on fine regions and leaves coarse
    ones bald - the classic giveaway."""
    from seamkiln.finishing import fur

    garment, result = draped(body, sdf)
    thin = fur(result.points, garment.triangles, density_per_cm2=2.0)
    thick = fur(result.points, garment.triangles, density_per_cm2=8.0)
    assert thick.summary()["strands"] == pytest.approx(thin.summary()["strands"] * 4, rel=0.02)
    assert thick.summary()["strands_per_second"] > 100_000, "not real-time"
    # deterministic
    again = fur(result.points, garment.triangles, density_per_cm2=2.0)
    assert np.allclose(thin.ends, again.ends)


# -- materials ---------------------------------------------------------------


def test_the_library_filters_by_what_a_cloth_is_for() -> None:
    from seamkiln import materials

    assert materials.library("denim")
    assert materials.category_of("cotton_poplin") == "shirting"
    with pytest.raises(KeyError, match="categories"):
        materials.library("velvet")


def test_a_card_that_is_not_a_cloth_refuses() -> None:
    from seamkiln import materials

    with pytest.raises(materials.MaterialError, match="different units"):
        materials.validate(Fabric("brick", 9000.0, 0.5, 1, 1, 1, 100, 100))
    with pytest.raises(materials.MaterialError, match="wearing a lab coat"):
        materials.validate(Fabric("claim", 200.0, 0.5, 1, 1, 1, 100, 100, tier=Tier.MEASURED))


def test_deriving_a_variant_drops_the_tier() -> None:
    """A measured denim's test report does not describe a denim you made 20%
    heavier."""
    from seamkiln import materials

    heavier = materials.derive("denim_12oz", "denim_16oz_t", gsm=540.0)
    assert heavier.tier is Tier.PLAUSIBLE
    assert heavier.gsm == 540.0
    assert heavier.compliances()["bending"] > fabric("denim_12oz").compliances()["bending"]


def test_materials_round_trip_through_a_file(tmp_path) -> None:
    from seamkiln import materials

    written = materials.to_file(["denim_12oz", "chiffon"], tmp_path / "lib.json")
    assert written["cards"] == 2
    assert set(materials.from_file(tmp_path / "lib.json", overwrite=True)) == {
        "denim_12oz",
        "chiffon",
    }
    with pytest.raises(materials.MaterialError, match="not a seamkiln material file"):
        (tmp_path / "bad.json").write_text('{"nope": 1}')
        materials.from_file(tmp_path / "bad.json")


# -- animation ---------------------------------------------------------------


def test_a_track_interpolates_smoothly() -> None:
    track = BlendTrack().record(0.0, "a", weight=0.2).record(2.0, "b", weight=0.8)
    assert track.at(0.0)["weight"] == pytest.approx(0.2)
    assert track.at(2.0)["weight"] == pytest.approx(0.8)
    assert track.at(1.0)["weight"] == pytest.approx(0.5)
    # smoothstep: the ends are flat, so the shape does not jerk into motion
    assert track.at(0.1)["weight"] < 0.2 + 0.6 * 0.05
    assert len(track.sample(fps=4.0)) == 9


def test_a_track_refuses_a_channel_it_does_not_have() -> None:
    with pytest.raises(ValueError, match="unknown blend shape"):
        Keyframe(0.0, {"wingspan": 0.5})
    with pytest.raises(ValueError, match="cannot branch"):
        BlendTrack([Keyframe(1.0, {"weight": 0.1}), Keyframe(1.0, {"weight": 0.9})])


def test_the_garment_is_dragged_along_the_track_not_re_draped(body, sdf) -> None:
    """Re-draping each frame pops between shapes; continuing the solve gives
    a garment that is dragged by the body changing under it."""
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=26.0)
    track = BlendTrack().record(0.0, "slim", weight=0.2).record(1.0, "fuller", weight=0.9)

    def stand_in(values):
        return mannequin(height=1.75, chest=0.90 + 0.30 * values.get("weight", 0.5))

    frames = animate(
        garment,
        track,
        fabric="cotton_jersey",
        fps=3.0,
        frames_per_step=30,
        voxel_mm=16.0,
        body_factory=stand_in,
        settings=DrapeSettings(frames=30, substeps=10),
    )
    report = animation_report(frames)
    assert report["frames"] == 4
    assert report["worn_throughout"] is True
    assert 0.0 < report["rebake_share"] < 1.0
    # the hem rides UP as the body fills out, which is what clothes do
    assert frames[-1].points[:, 1].min() > frames[0].points[:, 1].min()


def test_an_empty_track_animates_nothing(body) -> None:
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=20.0)
    with pytest.raises(ValueError, match="animates nothing"):
        animate(garment, BlendTrack())
