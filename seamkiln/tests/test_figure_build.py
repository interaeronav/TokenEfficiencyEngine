"""The figure's two builds: the male one it always had, bit for bit, and a
female one derived from measured sex differences.

The female build is not a taste: each proportion is the male figure's
fraction of stature times the female/male ratio of (mean / stature) from
ANSUR II (2012, 1,986 women and 4,082 men, public data), so the figure's
stylisation stays and only what the survey says differs between the sexes
moves. These tests hold the arithmetic to the survey and the male build to
its history.
"""

from __future__ import annotations

from hashlib import sha256

import numpy as np
import pytest

from seamkiln.avatar import Pose
from seamkiln.figure import (
    ANSUR_II,
    FEMALE,
    MALE,
    build,
    chest_girth_m,
    figure,
    fitted_to_chest,
    joints,
    shape_ratio,
    trunk_girth_m,
)
from seamkiln.session import Command, CommandError, Session

H = 1.65


def _mesh_digest(mesh) -> str:
    return sha256(np.round(np.asarray(mesh.vertices), 9).tobytes()).hexdigest()[:16]


def test_the_male_build_is_the_figure_as_it_was() -> None:
    """Every A65 number was measured on this mesh; the build parameter must
    not move a vertex of it. The digest was taken from the committed figure
    before builds existed (commit 74ca576)."""
    rest, a = figure(Pose(), height=1.80), figure(Pose.a_pose(), height=1.75, facing_deg=15.0)
    assert figure(Pose(), height=1.80, build="male").vertices.tobytes() == rest.vertices.tobytes()
    assert _mesh_digest(rest) == "8244edd0dbca383f"
    assert _mesh_digest(a) == "4baa5771e2cae3c1"
    assert joints(Pose(), height=1.80)["build"] == "male"


def test_the_female_build_follows_the_survey_ratios() -> None:
    """Trunk girths at the same joint heights, female over male, land on the
    survey's female/male shape ratios; so do the shoulders, arms and neck."""
    male, female = figure(Pose.a_pose(), height=H), figure(Pose.a_pose(), height=H, build="female")
    jm, jf = joints(Pose.a_pose(), height=H), joints(Pose.a_pose(), height=H, build="female")
    for joint, dimension in (("chest", "chestcircumference"), ("waist", "waistcircumference")):
        got = trunk_girth_m(female, jf[joint][1]) / trunk_girth_m(male, jm[joint][1])
        assert got == pytest.approx(shape_ratio(dimension), abs=0.015), (joint, got)
    hips = trunk_girth_m(female, jf["pelvis"][1] - 0.02) / trunk_girth_m(
        male, jm["pelvis"][1] - 0.02
    )
    assert hips == pytest.approx(shape_ratio("buttockcircumference"), abs=0.015)
    assert FEMALE.shoulder_half / MALE.shoulder_half == pytest.approx(
        shape_ratio("biacromialbreadth")
    )
    assert FEMALE.upper_arm_r / MALE.upper_arm_r == pytest.approx(
        shape_ratio("bicepscircumferenceflexed")
    )
    assert FEMALE.neck_r_top / MALE.neck_r_top == pytest.approx(shape_ratio("neckcircumference"))
    assert FEMALE.head_r / MALE.head_r == pytest.approx(shape_ratio("headcircumference"))
    assert shape_ratio("biacromialbreadth") < 0.96 < 1.06 < shape_ratio("buttockcircumference")
    assert female.is_watertight and female.metadata["seamkiln_figure"]["build"] == "female"


def test_the_survey_rows_are_the_published_means() -> None:
    """A spot check against the survey's own headline numbers: women 1628 mm
    tall with a 947 mm chest, men 1756 with 1059."""
    assert ANSUR_II["stature"] == (1628.5, 1756.2)
    assert ANSUR_II["chestcircumference"] == (946.9, 1058.7)
    assert shape_ratio("chestcircumference") == pytest.approx(0.9645, abs=0.001)


def test_a_chest_girth_fits_the_trunk_and_is_measured_where_cloth_touches() -> None:
    """`chest_m` is the widest trunk slice, read off the built mesh; the
    passes land within 5 mm on either build, and the rest of the body
    follows the chest by the survey's slopes: the shoulder joints barely,
    the upper arm and the waist strongly, the lengths not at all."""
    for name in ("female", "male"):
        fitted = figure(Pose.a_pose(), height=H, build=name, chest_m=0.86)
        assert chest_girth_m(fitted) == pytest.approx(0.86, abs=0.005), name
        untouched = build(name)
        got = fitted_to_chest(untouched, H, 0.86, pose=Pose.a_pose())
        k = got.chest_r / untouched.chest_r
        assert k < 1.0
        slopes = untouched.allometry
        assert got.shoulder_half / untouched.shoulder_half == pytest.approx(
            k ** slopes["shoulder_half"]
        )
        assert got.upper_arm_r / untouched.upper_arm_r == pytest.approx(k ** slopes["upper_arm_r"])
        assert got.waist_r / untouched.waist_r == pytest.approx(k ** slopes["waist_r"])
        assert got.shoulder_half / untouched.shoulder_half > got.upper_arm_r / untouched.upper_arm_r
        assert got.head_r == untouched.head_r and got.upper_arm == untouched.upper_arm
    with pytest.raises(ValueError, match="girth in metres"):
        figure(Pose(), height=H, chest_m=86.0)


def test_an_unknown_build_is_refused_by_name() -> None:
    with pytest.raises(ValueError, match="no build 'elf'"):
        figure(Pose(), height=H, build="elf")


def test_the_session_records_the_build_and_replays_it() -> None:
    session = Session()
    report = session.apply(
        Command("body", {"kind": "figure", "stature_m": H, "build": "female", "chest_m": 0.86})
    )
    assert session.body_spec["build"] == "female"
    assert session.body_spec["chest_m"] == 0.86
    assert chest_girth_m(session.body) == pytest.approx(0.86, abs=0.005)
    assert report["kind"] == "figure"
    replayed = Session.replay(session.script())
    assert replayed.body.vertices.tobytes() == session.body.vertices.tobytes()
    with pytest.raises(CommandError, match="no build"):
        Session().apply(Command("body", {"kind": "figure", "build": "elf"}))
