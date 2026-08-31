"""ODM runs now report what they ACHIEVED, not just where they wrote.

`capture_reconstruct` answered with artifact paths and a duration, so a
caller could not tell 137-of-147 images from 12-of-147 — both write files
and both "succeed". The numbers were always there in ODM's own
odm_report/stats.json; TEE never read them.

Shapes here are taken from a real run: the Okongo DJI_0100 pass,
2026-08-31, 147 images at 4K.
"""

from __future__ import annotations

import json

from tee.capture import tools as captools

REAL_STATS = {  # the live run, trimmed to the keys TEE reads
    "reconstruction_statistics": {
        "reconstructed_shots_count": 137,
        "initial_shots_count": 147,
        "reconstructed_points_count": 123755,
        "reprojection_error": 0.612,
    }
    # note: no "gps_errors" key - that run had no GPS
}


def _project(tmp_path, stats=REAL_STATS):
    (tmp_path / "odm_report").mkdir(parents=True, exist_ok=True)
    (tmp_path / "odm_report" / "stats.json").write_text(json.dumps(stats))
    return tmp_path


def _quality(project, artifacts=None):
    return captools._odm_quality(project, artifacts or {})


def test_a_good_run_reports_its_numbers(tmp_path):
    q = _quality(_project(tmp_path))
    assert q["images_used"] == 137 and q["images_total"] == 147
    assert q["images_used_fraction"] == 0.932
    assert q["points"] == 123755
    assert q["reprojection_error_px"] == 0.612
    assert "warning" not in q  # 93% is a good run


def test_a_weak_run_says_the_capture_is_usually_the_limit(tmp_path):
    """The failure this project keeps meeting is bad overlap, not a bad
    engine. 12 of 31 was the real case that started the investigation."""
    stats = {"reconstruction_statistics": {
        "reconstructed_shots_count": 12, "initial_shots_count": 31}}  # fmt: skip
    q = _quality(_project(tmp_path, stats))
    assert q["images_used_fraction"] < captools.ODM_WEAK_FRACTION
    assert "12 of 31" in q["warning"]
    assert "capture, not the engine" in q["warning"]


def test_no_gps_is_stated_because_it_invalidates_every_distance(tmp_path):
    """Without GPS the reconstruction is geometrically fine and spatially
    meaningless. ODM still reports an 'area covered' in the arbitrary frame,
    which is exactly the number someone would quote at a site meeting."""
    q = _quality(_project(tmp_path))
    assert q["georeferenced"] is False
    assert "LOCAL" in q["frame"]
    assert "must not be reported as site measurements" in q["frame"]


def test_gps_present_flips_it(tmp_path):
    stats = dict(REAL_STATS, gps_errors={"mean": {"x": 0.1, "y": 0.1, "z": 0.2}})
    q = _quality(_project(tmp_path, stats))
    assert q["georeferenced"] is True
    assert "frame" not in q  # nothing to warn about


def test_a_thin_orthophoto_names_the_actual_cause(tmp_path, monkeypatch):
    """29% coverage on the real run, because the flight was a pan. An
    orthophoto is a map or it is not; a technically-valid mostly-empty one
    is the failure mode worth catching."""
    monkeypatch.setattr(captools, "_ortho_coverage", lambda p: 0.294)
    q = _quality(_project(tmp_path), {"orthophoto": "/x/ortho.tif"})
    assert q["orthophoto_coverage"] == 0.294
    assert "nadir coverage flown as a grid" in q["orthophoto_warning"]
    assert "cannot make a map" in q["orthophoto_warning"]


def test_missing_stats_degrades_quietly(tmp_path):
    """A finished reconstruction must never fail over its own report."""
    q = _quality(tmp_path)  # no odm_report at all
    assert q == {} or "images_used" not in q


def test_unreadable_stats_do_not_raise(tmp_path):
    (tmp_path / "odm_report").mkdir()
    (tmp_path / "odm_report" / "stats.json").write_text("{ not json")
    assert "images_used" not in _quality(tmp_path)


def test_the_thresholds_are_the_measured_ones():
    assert captools.ODM_WEAK_FRACTION == 0.75
    assert captools.ODM_THIN_ORTHO == 0.5
