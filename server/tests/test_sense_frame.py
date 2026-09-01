"""A51 P2/P3 — framing that is fitted, then checked.

`capture_look` placed its camera by `bbox_diagonal/2 * distance`, with no
lens set, so the fit knew nothing about the field of view or the frame's
aspect: a tall subject and a wide one at the same "distance" filled wildly
different fractions of frame, and nothing checked the result.

P2 solves the distance from the lens and aspect. P3 closes the loop with
the only instrument that can judge a rendered scene - the vision model. A
pixel heuristic cannot: during research, measuring "fraction of frame
filled" by brightness reported 100% at EVERY distance, because it was
measuring the backdrop.
"""

from __future__ import annotations

import pytest

from tee import senses
from tee.kernel.errors import TeeError


# -- the grade parser -------------------------------------------------------


def test_a_well_formed_grade_is_read():
    g = senses._parse_frame_verdict("FILL=35 CROPPED=no VERDICT=good")
    assert g["fill_percent"] == 35 and g["cropped"] is False
    assert g["verdict"] == "good" and g["usable"] is True


def test_prose_instead_of_the_form_is_marked_UNUSABLE_not_passed():
    """A model asked for a rigid form will sometimes write prose anyway.
    That is not a crash and it is emphatically not a pass - a loop that
    cannot tell the difference will 'converge' on noise."""
    g = senses._parse_frame_verdict("The chair looks nicely positioned in the shot.")
    assert g["usable"] is False
    assert "verdict" not in g


def test_a_partial_grade_still_counts():
    g = senses._parse_frame_verdict("FILL=12 - the subject is small")
    assert g["fill_percent"] == 12 and g["usable"] is True


def test_a_wild_fill_is_clamped():
    assert senses._parse_frame_verdict("FILL=900 VERDICT=good")["fill_percent"] == 100


# -- where the camera goes next --------------------------------------------


def test_good_framing_stops_the_loop():
    assert senses._next_distance(1.0, {"verdict": "good"}) is None


def test_too_far_moves_in_and_too_close_pulls_back():
    assert senses._next_distance(1.0, {"verdict": "too far", "fill_percent": 10}) < 1.0
    assert senses._next_distance(1.0, {"verdict": "too close"}) > 1.0


def test_cropped_always_pulls_back_whatever_else_it_said():
    """Cropping is the one failure that cannot be traded against fill."""
    assert senses._next_distance(1.0, {"verdict": "too far", "cropped": True}) > 1.0


def test_an_ungradeable_answer_does_not_move_the_camera():
    assert senses._next_distance(1.0, {"usable": False}) is None


# -- the loop's honesty -----------------------------------------------------


class _Adapter:
    """Renders nothing; grades come from the stubbed describe()."""

    def capture_look(self, max_bytes, **kw):
        return b"\xff\xd8" + b"x" * 64


def _stub_grades(monkeypatch, grades):
    seen = iter(grades)
    monkeypatch.setattr(senses, "describe", lambda *a, **k: {"answer": next(seen)})


def test_it_converges_and_says_so(monkeypatch):
    _stub_grades(
        monkeypatch, ["FILL=10 CROPPED=no VERDICT=too far", "FILL=40 CROPPED=no VERDICT=good"]
    )
    r = senses.frame({"distance": 3.0}, adapters={"blender": _Adapter()})
    assert r["converged"] is True
    assert len(r["attempts"]) == 2
    assert r["distance"] < 3.0
    assert "warning" not in r


def test_a_run_that_never_converges_says_that_too(monkeypatch):
    """The failure this prevents: returning the last frame as though it were
    the right one."""
    _stub_grades(monkeypatch, ["FILL=5 CROPPED=no VERDICT=too far"] * 4)
    r = senses.frame({"distance": 3.0, "max_retries": 2}, adapters={"blender": _Adapter()})
    assert r["converged"] is False
    assert "did not converge" in r["warning"]
    assert "best of them" in r["warning"]


def test_every_attempt_is_reported_with_its_grade(monkeypatch):
    _stub_grades(
        monkeypatch,
        [
            "FILL=8 CROPPED=no VERDICT=too far",
            "FILL=20 CROPPED=no VERDICT=too far",
            "FILL=45 CROPPED=no VERDICT=good",
        ],
    )
    r = senses.frame({"distance": 4.0}, adapters={"blender": _Adapter()})
    assert len(r["attempts"]) == 3
    for att in r["attempts"]:
        assert "distance" in att and "grade" in att


def test_the_verdict_is_labelled_advice_not_measurement(monkeypatch):
    _stub_grades(monkeypatch, ["FILL=40 CROPPED=no VERDICT=good"])
    r = senses.frame({}, adapters={"blender": _Adapter()})
    assert "advice rather than measurement" in r["note"]
    assert "local" in r["graded_by"]


def test_an_adapter_that_cannot_aim_refuses_by_name():
    class Blind:
        pass

    with pytest.raises(TeeError) as e:
        senses.frame({}, adapters={"godot": Blind()})
    assert e.value.code == "sense_no_aiming"
    assert "run_scene" in e.value.fix


def test_no_adapter_at_all_refuses():
    with pytest.raises(TeeError) as e:
        senses.frame({}, adapters={})
    assert e.value.code == "sense_no_adapter"


# -- P2: the fit is lens-aware ---------------------------------------------


def test_the_generated_program_solves_from_lens_and_aspect():
    """Asserted on the generated Blender source: the old line multiplied the
    bounding radius by a guess and set no lens at all."""
    from tee.adapters.blender import codegen

    src = codegen.program_capture_look(
        "/tmp/x.jpg",
        512,
        288,
        80,
        8,
        target="",
        azimuth_deg=45,
        elevation_deg=20,
        distance=1.0,
    )
    assert "cam_data.lens" in src
    assert "half_fov_x" in src and "half_fov_y" in src
    assert "TARGET_FILL" in src
    assert "radius = max((hi - lo).length / 2, 0.001) * max(float(" not in src
