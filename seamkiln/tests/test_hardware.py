"""Zippers and buttons: the parts, the physics, and the two-part fastener.

Every number asserted here was measured on the jacket block at a particle
distance that CONVERGES (9 mm on a 6 mm field). A claim about whether an
opening closed is exactly the kind of claim a coarse preview must not be
asked for.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from seamkiln.drape.body import mannequin, sdf_from_mesh
from seamkiln.drape.garment import build_garment, top_arrangement
from seamkiln.drape.solve import DrapeSettings, drape
from seamkiln.hardware import buttons as B
from seamkiln.hardware import zipper as Z
from seamkiln.hardware.trim import ZIPPER_TRIM, zipper_trim
from seamkiln.pattern.fixtures import jacket_block

PD = 9.0  # converges on this block; 12 mm leaves a 55 mm armhole gap
VOXEL = 6.0


@pytest.fixture(scope="module")
def rig():
    body = mannequin()
    return body, sdf_from_mesh(body, voxel_mm=VOXEL)


def _zip_garment(body, *, material="nylon", layout="one-way", sliders=None):
    pattern = jacket_block(opening="zipper")
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=PD)
    spec = Z.ZipperSpec(material=material, layout=layout)
    zipper = Z.install(garment, garment.points, seam_id="centre-front", spec=spec, sliders=sliders)
    return garment, zipper


# -- the opening ---------------------------------------------------------------


def test_an_opening_is_paired_but_not_sewn() -> None:
    """The whole trick. A zipper opening has to know which point faces which -
    that is a seam's job - while not being held shut, which is a seam's other
    job. `kind` splits the two."""
    body = mannequin()
    pattern = jacket_block(opening="zipper")
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=PD)

    assert garment.hardware_spans == {"centre-front": (0, garment.hardware_pairs.shape[0])}
    assert garment.hardware_kind["centre-front"] == "zipper"
    assert garment.hardware_pairs.shape[0] > 20
    # and NOT in the sewn set, which is the part that matters
    sewn = {tuple(sorted(p)) for p in garment.seams.tolist()}
    opening = {tuple(sorted(p)) for p in garment.hardware_pairs.tolist()}
    assert sewn.isdisjoint(opening)


def test_a_zipper_needs_its_opening_declared_on_the_pattern() -> None:
    from seamkiln.pattern.fixtures import tee_block

    body = mannequin()
    pattern = tee_block()
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=16.0)
    with pytest.raises(ValueError, match="pattern decision, not a drape decision"):
        Z.install(garment, garment.points, seam_id="centre-front")


def test_the_chain_runs_bottom_to_top(rig) -> None:
    """t = 0 is the bottom stop, and bottom means lower in the WORLD. Get it
    backwards and 'unzip to 0.2' opens the collar instead of the hem."""
    body, _ = rig
    garment, zipper = _zip_garment(body)
    mid = 0.5 * (garment.points[zipper.pairs[:, 0]] + garment.points[zipper.pairs[:, 1]])
    assert mid[0, 1] < mid[-1, 1]
    assert zipper.t[0] == pytest.approx(0.0, abs=1e-9)
    assert zipper.t[-1] == pytest.approx(1.0, abs=1e-9)
    assert np.all(np.diff(zipper.t) >= -1e-12)


# -- the sliders ---------------------------------------------------------------


def test_the_two_two_way_layouts_are_exact_complements() -> None:
    """Head-to-head opens the MIDDLE; bottom-to-bottom opens the ENDS. Stating
    it as 'they are complements' is the tidiest way to keep them straight, so
    it is asserted rather than left in a docstring."""
    t = np.linspace(0.0, 1.0, 101)
    hh = Z._engaged(t, "two-way-head-to-head", (0.3, 0.7))
    bb = Z._engaged(t, "two-way-bottom-to-bottom", (0.3, 0.7))
    # complements everywhere except the two slider positions, which both own
    assert int((hh == bb).sum()) <= 2
    assert hh[0] and hh[-1] and not hh[50]
    assert bb[50] and not bb[0] and not bb[-1]


def test_a_one_way_slider_closes_below_itself() -> None:
    t = np.linspace(0.0, 1.0, 11)
    assert Z._engaged(t, "one-way", (1.0,)).all()
    assert not Z._engaged(t, "one-way", (0.0,))[1:].any()
    assert int(Z._engaged(t, "one-way", (0.5,)).sum()) == 6


def test_dragging_the_slider_opens_the_opening(rig) -> None:
    """The interactive gesture, measured: engaged pairs sit at the chain's own
    width, unengaged pairs hang open, and the slider is what decides which."""
    body, field = rig
    seen = []
    for at in (1.0, 0.5, 0.0):
        garment, zipper = _zip_garment(body, material="metal")
        Z.unzip(zipper, to=at)
        Z.apply(garment, zipper)
        result = drape(garment, field, fabric="cotton_poplin", settings=DrapeSettings(frames=280))
        assert result.report()["converged"] is True
        gap = (
            np.linalg.norm(
                result.points[zipper.pairs[:, 0]] - result.points[zipper.pairs[:, 1]], axis=1
            )
            * 1000.0
        )
        mask = zipper.engaged()
        closed = float(gap[mask].mean()) if mask.any() else float("nan")
        opened = float(gap[~mask].mean()) if (~mask).any() else float("nan")
        seen.append((at, closed, opened, float(gap.sum())))
        if mask.any():
            # a #5 chain holds its two edges 5 mm apart - the teeth have a size
            assert closed < 10.0, f"slider at {at}: closed part sits at {closed:.1f} mm"
        if (~mask).any():
            assert opened > 100.0, f"slider at {at}: open part only reached {opened:.1f} mm"
    # and more open as the slider comes down: the opening's TOTAL width, not
    # the mean of whichever pairs happen to be unengaged - the fully open front
    # averages in the pairs the shoulders hold close (159 mm) against the
    # half-open front's hem-only 171, and a mean over different sets is not a
    # claim about the garment
    assert seen[2][3] > seen[1][3] > seen[0][3], [s[3] for s in seen]


def test_a_slider_that_does_not_exist_is_refused(rig) -> None:
    body, _ = rig
    _, zipper = _zip_garment(body)
    with pytest.raises(ValueError, match="there is no slider 1"):
        Z.unzip(zipper, to=0.5, slider=1)
    with pytest.raises(ValueError, match=r"within 0\.\.1"):
        Z.unzip(zipper, to=1.4)


# -- the chain, as a physical object -------------------------------------------


def test_a_closed_chain_rests_on_the_flat_pattern_not_on_the_pose(rig) -> None:
    """The bug this exists to stop. Measuring the cross-braces in the CURRENT
    arrangement - the arrangement with the opening hanging open - made them
    hold it open: 50 engaged pairs at a 204 mm gap, while a single engaged
    pair closed to 5.0 mm. A constraint that learns its rest length from a
    wrong pose preserves the wrong pose."""
    body, _ = rig
    garment, zipper = _zip_garment(body)
    Z.apply(garment, zipper)
    block = garment.attachments["zip:centre-front"]
    rungs = block.rest[: len(zipper)]
    assert np.allclose(rungs, zipper.spec.size / 1000.0)
    # every ladder member is chain-sized or step-sized, never opening-sized
    assert block.rest.max() < 0.05, "a ladder member is resting at the OPEN width"


def test_a_zipper_weighs_what_it_is_made_of(rig) -> None:
    """A #5 brass chain is 33 g/m and a nylon coil is 10 g/m; on a 590 mm
    opening that is 23 g against 7 g. Hardware that does not weigh anything
    drapes like a decal."""
    body, _ = rig
    masses = {}
    for material in ("nylon", "plastic", "metal"):
        garment, zipper = _zip_garment(body, material=material)
        Z.apply(garment, zipper)
        masses[material] = zipper.mass_kg() * 1000.0
        # and it reaches the solver, not just the summary
        assert garment.added_mass_kg().sum() == pytest.approx(zipper.mass_kg(), rel=1e-9)
    assert masses["nylon"] < masses["plastic"] < masses["metal"]
    assert masses["metal"] / masses["nylon"] == pytest.approx(3.2, abs=0.2)
    # an UNZIPPED zipper still weighs what it weighs
    garment, zipper = _zip_garment(body, material="metal")
    Z.unzip(zipper, to=0.0)
    Z.apply(garment, zipper)
    assert garment.added_mass_kg().sum() == pytest.approx(zipper.mass_kg(), rel=1e-9)


def test_chain_size_scales_the_mass_by_the_square(rig) -> None:
    """#10 is twice the width of #5 and four times the metal, because mass
    goes with the cross-section."""
    assert zipper_trim("metal", 10.0).chain_g_per_m == pytest.approx(
        4.0 * ZIPPER_TRIM["metal"].chain_g_per_m
    )
    assert zipper_trim("nylon", 3.0).chain_g_per_m == pytest.approx(
        0.36 * ZIPPER_TRIM["nylon"].chain_g_per_m
    )


def test_a_stiffer_chain_bends_less_when_its_weight_is_held_constant(rig) -> None:
    """The honest form of this claim. With mass held constant a stiffer chain
    demonstrably wiggles less: 2216 deg of total turn at x1 against 2012 at
    x6.5, from 2320 with no straighteners at all.

    With the REAL materials the order is not monotone, because a brass chain
    is both 6.5x stiffer and 3.2x heavier than a nylon coil and on a hanging
    opening those fight. Both effects are modelled; this test isolates the
    one it names."""
    body, field = rig

    def total_turn(stiffness: float | None) -> float:
        garment, zipper = _zip_garment(body)
        if stiffness is None:
            Z.apply(garment, zipper)
            garment.detach("zip:centre-front:bend")
        else:
            zipper.trim = dataclasses.replace(zipper.trim, stiffness=stiffness)
            Z.apply(garment, zipper)
        result = drape(garment, field, fabric="cotton_poplin", settings=DrapeSettings(frames=280))
        chain = 0.5 * (result.points[zipper.pairs[:, 0]] + result.points[zipper.pairs[:, 1]])
        step = np.diff(chain, axis=0)
        step /= np.linalg.norm(step, axis=1, keepdims=True)
        return float(np.degrees(np.arccos(np.clip((step[:-1] * step[1:]).sum(1), -1, 1))).sum())

    free, soft, stiff = total_turn(None), total_turn(1.0), total_turn(6.5)
    assert stiff < soft < free, f"free {free:.0f}, soft {soft:.0f}, stiff {stiff:.0f}"
    assert free - stiff > 100.0


def test_the_parts_are_all_generated(rig) -> None:
    """Tape, teeth, chain, slider, puller, stopper - the user asked for each
    by name, so each is asserted by name."""
    body, _ = rig
    garment, zipper = _zip_garment(body, material="plastic")
    parts = Z.geometry(zipper, garment.points)
    for name in ("tape_left", "tape_right", "chain", "teeth", "sliders", "pullers", "stops"):
        assert parts[name].shape[0] > 0, f"no {name}"
    # teeth at the MATERIAL's pitch, not one per particle
    expected = zipper.length_m * 1000.0 / zipper.trim.teeth_pitch_mm
    assert parts["teeth"].shape[0] == pytest.approx(expected, rel=0.02)
    # the tapes sit outside the chain, on opposite sides
    left = parts["tape_left"] - parts["chain"]
    right = parts["tape_right"] - parts["chain"]
    assert np.all((left * right).sum(axis=1) < 0.0)
    # and the puller hangs BELOW its slider, which is how you see which way up
    assert parts["pullers"][0][1] < parts["sliders"][0][1]


def test_two_sliders_for_a_two_way_and_one_for_a_one_way(rig) -> None:
    body, _ = rig
    _, one = _zip_garment(body)
    _, two = _zip_garment(body, layout="two-way-head-to-head")
    assert one.spec.sliders == 1 and two.spec.sliders == 2
    assert len(two.sliders) == 2
    assert two.open_fraction() == pytest.approx(0.0, abs=1e-9)  # closed by default


def test_an_unknown_layout_or_material_names_the_known_ones() -> None:
    with pytest.raises(ValueError, match="two-way-head-to-head"):
        Z.ZipperSpec(layout="sideways")
    with pytest.raises(ValueError, match="metal"):
        zipper_trim("unobtainium")


# -- buttons -------------------------------------------------------------------


def _placket(body, *, kind="4-hole", pd=PD, ligne=24.0, rows=(120.0, 240.0, 360.0, 480.0)):
    pattern = jacket_block(opening="placket")
    garment = build_garment(pattern, top_arrangement(pattern, body), particle_distance=pd)
    spec = B.ButtonSpec(kind=kind, ligne=ligne)
    fastenings = [
        B.fasten(
            garment,
            B.place(garment, garment.points, panel="FRONT_R", at=(14.0, y)),
            B.hole(garment, panel="FRONT_L", at=(-14.0, y), button=spec),
            button=spec,
            id=f"b{y:.0f}",
        )
        for y in rows
    ]
    B.apply(garment, fastenings)
    return garment, fastenings


def test_a_button_weighs_what_a_button_weighs() -> None:
    """A 24L polyester 4-hole comes out at 0.755 g from its own volume - not
    from a number anybody typed. A real shirt button is 0.6-0.9 g."""
    assert B.ButtonSpec().mass_kg() * 1000.0 == pytest.approx(0.755, abs=0.03)
    assert B.ButtonSpec(material="metal").mass_kg() > 5 * B.ButtonSpec().mass_kg()
    # 24 ligne is 15.24 mm, because a ligne is 0.635 mm and always has been
    assert B.ButtonSpec().diameter_mm == pytest.approx(15.24, abs=0.01)
    # a shank stands the button off; a flat one does not
    assert B.ButtonSpec(kind="shank").shank_mm > 0.0
    assert B.ButtonSpec(kind="toggle").shank_mm > 0.0
    assert B.ButtonSpec(kind="2-hole").shank_mm == 0.0


def test_every_advertised_button_type_exists() -> None:
    for kind in ("2-hole", "4-hole", "shank", "snap", "rivet", "toggle"):
        assert B.ButtonSpec(kind=kind).kind == kind
    with pytest.raises(ValueError, match="4-hole"):
        B.ButtonSpec(kind="velcro")


def test_a_button_will_not_pass_a_hole_that_is_too_small() -> None:
    """15.2 mm of button and 14 mm of hole look fine on a screen and cannot be
    done up on a body. The refusal names the size to cut."""
    body = mannequin()
    garment, _ = _placket(body, rows=(240.0,))
    spec = B.ButtonSpec()
    tight = B.hole(garment, panel="FRONT_L", at=(-14.0, 300.0), button=spec, length_mm=14.0)
    with pytest.raises(ValueError, match=r"Cut the hole to 18\.2 mm"):
        B.fasten(garment, 0, tight, button=spec)


def test_fastening_pulls_the_placket_together_and_holds_it(rig) -> None:
    """The Fasten Button gesture, measured. The two panels end up a shank plus
    two cloth thicknesses apart - NOT at zero, which would be the fabric
    occupying the same space as itself."""
    body, field = rig
    garment, fastenings = _placket(body)
    result = drape(garment, field, fabric="cotton_poplin", settings=DrapeSettings(frames=280))
    assert result.report()["converged"] is True
    spans = (
        np.asarray(
            [
                np.linalg.norm(result.points[f.button_at] - result.points[f.hole.index])
                for f in fastenings
            ]
        )
        * 1000.0
    )
    target = fastenings[0].stand_off_m * 1000.0
    assert target == pytest.approx(3.2, abs=0.05)
    assert spans.min() > 1.0, "a fastened placket is not at zero separation"
    assert spans.max() < 4.0 * target, f"a button let go: {spans.round(1).tolist()}"


def test_an_unfastened_placket_falls_open(rig) -> None:
    """The control. Without the buttons the same two edges hang apart, which
    is what makes the previous test about the buttons and not about the cloth."""
    body, field = rig
    garment, fastenings = _placket(body)
    garment.detach("buttons")
    garment.detach("buttons:rim")
    result = drape(garment, field, fabric="cotton_poplin", settings=DrapeSettings(frames=280))
    spans = (
        np.asarray(
            [
                np.linalg.norm(result.points[f.button_at] - result.points[f.hole.index])
                for f in fastenings
            ]
        )
        * 1000.0
    )
    assert spans.mean() > 40.0, f"the placket stayed shut with no buttons: {spans.round(1)}"


def test_a_rivet_refuses_to_be_undone(rig) -> None:
    body, _ = rig
    _, fastenings = _placket(body, kind="rivet", rows=(240.0,))
    with pytest.raises(ValueError, match="that is what makes it a rivet"):
        B.unfasten(fastenings[0])
    _, sewn = _placket(body, kind="2-hole", rows=(240.0,))
    assert B.unfasten(sewn[0]).popped is True


def test_a_button_the_mesh_cannot_resolve_says_so(rig) -> None:
    """A 15.2 mm button on a 9 mm mesh has no cloth inside its own footprint,
    so its collision rim cannot be built. That is reported, with the mesh that
    would fix it - it is not silently skipped."""
    body, _ = rig
    _, coarse = _placket(body, pd=PD)
    assert all("rim_unresolved" in f.meta for f in coarse)
    assert "5 mm or finer" in coarse[0].meta["rim_unresolved"]
    _, fine = _placket(body, pd=5.0, rows=(240.0,))
    assert "rim_unresolved" not in fine[0].meta


def test_a_custom_button_is_weighed_not_declared(tmp_path) -> None:
    """A studio's own button arrives as an OBJ, and its WEIGHT comes off the
    mesh. That is the whole reason to register geometry rather than a number."""
    trimesh = pytest.importorskip("trimesh")
    disc = trimesh.creation.cylinder(radius=9.0, height=3.4, sections=48)
    path = tmp_path / "chunky.obj"
    disc.export(path)
    spec = B.register_obj(path, material="horn")
    assert spec.diameter_mm == pytest.approx(18.0, rel=0.02)
    assert spec.thickness_mm == pytest.approx(3.4, rel=0.02)
    expected = np.pi * 0.009**2 * 0.0034 * 1300.0 * 1000.0
    assert spec.mass_g == pytest.approx(expected, rel=0.03)
    assert spec.mesh_path == str(path)


def test_a_custom_buttonhole_mask_reads_black_as_the_hole(tmp_path) -> None:
    """Black is the hole; transparent is nothing. Treating transparent as hole
    would make every PNG one enormous buttonhole, and it would be silent."""
    Image = pytest.importorskip("PIL.Image", reason="pillow")
    rgba = np.zeros((80, 80, 4), dtype=np.uint8)
    rgba[36:44, 20:60, 3] = 255  # opaque, and black: a 40 x 8 px slit
    Image.fromarray(rgba, "RGBA").save(tmp_path / "slit.png")
    info = B.register_mask(tmp_path / "slit.png", pixels_per_mm=4.0)
    assert info["length_mm"] == pytest.approx(10.0, abs=0.3)
    assert info["width_mm"] == pytest.approx(2.0, abs=0.3)
    assert info["angle_deg"] == 0.0

    white = np.zeros((40, 40, 4), dtype=np.uint8)
    white[..., :3] = 255
    white[..., 3] = 255
    Image.fromarray(white, "RGBA").save(tmp_path / "blank.png")
    with pytest.raises(ValueError, match="no opaque dark pixels"):
        B.register_mask(tmp_path / "blank.png")
