"""The DJI-spectrum resolver's four fixture paths (A42 T2 acceptance):
electronic (matched correction), mechanical (correction off), RTK-stamped
(band tightens to the std fields), unknown (honest fallback) — plus the
multi-camera split and the gimbal/AGL priors."""

from __future__ import annotations

import pytest
from fixtures_capture import write_dji_jpeg

from tee.capture import dji
from tee.kernel.errors import TeeError

pytest.importorskip("PIL")


def test_electronic_shutter_gets_matched_correction(tmp_path):
    files = [
        write_dji_jpeg(
            tmp_path / f"e{i}.jpg",
            "FC3582",
            GimbalPitchDegree="-89.90",
            RelativeAltitude="+45.20",
        )
        for i in range(3)
    ]
    result = dji.resolve_set(files)
    (entry,) = result["sets"]
    assert entry["model"] == "DJI Mini 3 Pro"
    assert entry["shutter"] == "electronic"
    assert entry["correction"]["mode"] == "matched"
    assert entry["positioning"] == "gnss"
    assert entry["priors"]["gimbal_pitch_deg"] == -89.9
    assert entry["priors"]["relative_altitude_m"] == 45.2


def test_mechanical_shutter_runs_correction_off(tmp_path):
    result = dji.resolve_set([write_dji_jpeg(tmp_path / "m.jpg", "FC6310")])
    (entry,) = result["sets"]
    assert entry["model"] == "DJI Phantom 4 Pro"
    assert entry["correction"] == {"mode": "off", "why": "mechanical shutter needs none"}


def test_rtk_band_tightens_only_when_files_prove_it(tmp_path):
    stamped = [
        write_dji_jpeg(
            tmp_path / f"r{i}.jpg",
            "FC6310R",
            RtkStdLat="0.02",
            RtkStdLon="0.02",
            RtkStdHgt="0.03",
        )
        for i in range(2)
    ]
    result = dji.resolve_set(stamped)
    (entry,) = result["sets"]
    assert entry["positioning"] == "rtk"
    assert entry["band"] == "rtk ±3 cm (from RtkStd fields, worst of set)"

    # one unstamped file in the set -> the band does NOT tighten
    mixed = [*stamped, write_dji_jpeg(tmp_path / "r9.jpg", "FC6310R")]
    (entry,) = dji.resolve_set(mixed)["sets"]
    assert entry["positioning"] == "gnss"
    assert "2/3" in entry["band"]


def test_unknown_code_degrades_honestly(tmp_path):
    result = dji.resolve_set([write_dji_jpeg(tmp_path / "u.jpg", "FC9999")])
    (entry,) = result["sets"]
    assert entry["model"] == "unknown"
    assert entry["correction"]["mode"] == "off"
    assert "fly slow" in entry["correction"]["why"]
    assert entry["band"] == "meters-class absolute (consumer GNSS)"


def test_multi_camera_set_splits_per_code(tmp_path):
    files = [
        write_dji_jpeg(tmp_path / "wide.jpg", "L2D-20C"),
        write_dji_jpeg(tmp_path / "tele.jpg", "FC4382"),
    ]
    result = dji.resolve_set(files)
    assert result["split_by_camera"] is True
    assert [s["camera_code"] for s in result["sets"]] == ["FC4382", "L2D-20C"]


def test_empty_set_and_missing_file_refuse_loudly(tmp_path):
    with pytest.raises(TeeError) as excinfo:
        dji.resolve_set([])
    assert excinfo.value.code == "capture_empty_set"
    with pytest.raises(TeeError) as excinfo:
        dji.resolve_set([tmp_path / "absent.jpg"])
    assert excinfo.value.code == "capture_missing_file"
