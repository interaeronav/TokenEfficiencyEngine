"""A45 P2c — DICOM archives (Orthanc, over HTTP) and volumes (MONAI).

The archive tests need a live Orthanc and skip cleanly without one. The
PHI tests do not need a server: withholding identifiers is a property of
TEE's own code and is asserted directly, because it is the one behaviour
that must never regress quietly.
"""

from __future__ import annotations

import pathlib
import tempfile
import urllib.error
import urllib.request

import pytest

from tee.fleet import med, probe
from tee.kernel.errors import TeeError

ORTHANC = {"url": "http://127.0.0.1:8042", "username": "orthanc", "password": "tee-local"}


def _archive_up() -> bool:
    try:
        urllib.request.urlopen(f"{ORTHANC['url']}/system", timeout=2)
    except urllib.error.HTTPError:
        return True  # 401 still means something is listening
    except Exception:
        return False
    return True


needs_archive = pytest.mark.skipif(
    not _archive_up(),
    reason="no Orthanc on :8042 - docker run -d -p 8042:8042 "
    "-e ORTHANC_PASSWORD=tee-local orthancteam/orthanc:latest",
)
needs_monai = pytest.mark.skipif(not probe.have("monai"), reason="[medimg] extra not installed")


# -- PHI: server-free, and non-negotiable -----------------------------------


def test_phi_tags_are_stripped_by_default():
    tags = {
        "PatientName": "DOE^JANE",
        "PatientID": "12345",
        "PatientBirthDate": "19700101",
        "StudyDescription": "CT HEAD",
        "Modality": "CT",
    }
    out = med._strip_phi(dict(tags), phi=False)
    assert "PatientName" not in out
    assert "PatientID" not in out
    assert "PatientBirthDate" not in out
    assert out["StudyDescription"] == "CT HEAD", "clinical content must survive"
    assert out["Modality"] == "CT"


def test_phi_is_returned_only_when_explicitly_asked():
    tags = {"PatientName": "DOE^JANE", "Modality": "CT"}
    assert med._strip_phi(dict(tags), phi=True) == tags


def test_the_phi_set_covers_the_direct_identifiers():
    for t in (
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "AccessionNumber",
        "ReferringPhysicianName",
    ):
        assert t in med.PHI_TAGS, t


def test_orthanc_level_names_are_spelled_out_not_derived():
    """Deriving 'Study' from 'studies' by slicing produced 'Studie' and a
    400 from a live server. Protocol vocabularies are not regular."""
    assert med.LEVELS["studies"] == "Study"
    assert med.LEVELS["series"] == "Series"
    assert med.LEVELS["instances"] == "Instance"
    assert med.LEVELS["patients"] == "Patient"


# -- refusals ---------------------------------------------------------------


def test_write_verbs_are_refused_before_any_request():
    with pytest.raises(TeeError) as e:
        med._call({"url": "http://127.0.0.1:1"}, "/studies/x", method="DELETE")
    assert e.value.code == "med_forbidden_method"
    assert "does not modify or delete" in e.value.fix


def test_an_absent_archive_refuses_with_the_docker_line():
    with pytest.raises(TeeError) as e:
        med.system({"url": "http://127.0.0.1:1"})
    assert e.value.code == "med_unreachable"
    assert "orthancteam/orthanc" in e.value.fix
    assert "GPLv3" in e.value.fix, "say why TEE does not bundle it"


def test_missing_ids_refuse_with_where_to_get_one():
    with pytest.raises(TeeError) as e:
        med.study_tree({"url": ORTHANC["url"]})
    assert "med_find_studies" in e.value.fix
    with pytest.raises(TeeError) as e:
        med.instance_tags({"url": ORTHANC["url"]})
    assert "med_study_tree" in e.value.fix


# -- against a live archive -------------------------------------------------


@needs_archive
def test_the_archive_answers_with_counts_and_plugins():
    s = med.system(dict(ORTHANC))
    assert s["ok"] is True
    assert s["api_version"] >= 1
    assert set(s["counts"]) == {"patients", "studies", "series", "instances"}
    assert isinstance(s["plugins"], list)


@needs_archive
def test_studies_come_back_with_usable_ids_and_no_phi():
    f = med.find_studies(dict(ORTHANC, limit=5))
    if f["total"] == 0:
        pytest.skip("archive is empty - upload a study to exercise this")
    row = f["studies"][0]
    assert len(row["id"]) > 30, "a truncated id is not an id - it must round-trip"
    assert not (set(row) & med.PHI_TAGS), f"PHI leaked into a study row: {row}"
    assert "phi" in f

    # and the id genuinely works as a handle
    tree = med.study_tree(dict(ORTHANC, study_id=row["id"]))
    assert tree["study_id"] == row["id"]
    assert tree["n_series"] >= 1


@needs_archive
def test_instance_tags_never_include_pixel_data():
    f = med.find_studies(dict(ORTHANC, limit=1))
    if f["total"] == 0:
        pytest.skip("archive is empty")
    tree = med.study_tree(dict(ORTHANC, study_id=f["studies"][0]["id"]))
    series = med._call(ORTHANC, f"/series/{tree['series'][0]['id']}")
    iid = (series.get("Instances") or [None])[0]
    tags = med.instance_tags(dict(ORTHANC, instance_id=iid))
    assert "PixelData" not in tags["tags"]
    assert not (set(tags["tags"]) & med.PHI_TAGS)
    assert tags["n_tags"] > 5


# -- MONAI ------------------------------------------------------------------


@needs_monai
def test_volume_stats_reports_scalars_not_the_array(tmp_path):
    """A known array: stats must be exact, and the array must not appear."""
    import numpy as np

    vol = np.zeros((8, 8, 4), dtype=np.float32)
    vol[0, 0, 0] = 100.0
    vol[1, 1, 1] = -50.0
    path = tmp_path / "vol.npy"
    np.save(path, vol)

    r = med.volume_stats({"path": str(path)})
    assert r["shape"] == [8, 8, 4]
    assert r["voxels"] == 256
    assert r["max"] == pytest.approx(100.0)
    assert r["min"] == pytest.approx(-50.0)
    assert r["nonzero_fraction"] == pytest.approx(2 / 256, abs=1e-6)
    payload = repr(r)
    assert "0.0, 0.0, 0.0" not in payload, "the voxel array must never be serialised"


@needs_monai
def test_an_unreadable_path_names_the_reader_packages(tmp_path):
    bad = tmp_path / "not-an-image.xyz"
    bad.write_text("nope")
    with pytest.raises(TeeError) as e:
        med.volume_stats({"path": str(bad)})
    assert e.value.code == "med_unreadable"
    assert "medimg" in e.value.fix


def test_volume_stats_requires_a_path():
    with pytest.raises(TeeError) as e:
        med.volume_stats({})
    assert "path is required" in e.value.message


# -- registration -----------------------------------------------------------


def test_med_tools_register_on_read_medimg():
    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    names = [
        "med_archive",
        "med_find_studies",
        "med_study_tree",
        "med_instance_tags",
        "med_volume_stats",
        "med_backends",
    ]
    for n in names:
        assert n in app.registry._tools, n
        assert app.registry._tools[n].capability == "read-medimg"


def test_backends_reports_both_halves_without_a_server():
    r = med.backends({"url": "http://127.0.0.1:1"})
    assert "libraries" in r
    assert r["orthanc"]["reachable"] is False
    assert "orthancteam" in r["orthanc"]["fix"]


def test_probe_schemas_accept_the_same_credentials_as_their_tools():
    """med_backends declared only `url` while every other med_ tool took
    username/password - so the probe could not reach an authenticated
    archive, which is every real one. Caught by calling it for real."""
    import tempfile

    from tee.app import TeeApp

    app = TeeApp({}, project_root=tempfile.mkdtemp())
    for name in ("med_archive", "med_find_studies", "med_study_tree", "med_backends"):
        props = set(app.registry._tools[name].schema.get("properties", {}))
        assert {"url", "username", "password"} <= props, f"{name} is missing credentials"
    bi_props = set(app.registry._tools["bi_probe"].schema.get("properties", {}))
    assert {"url", "token"} <= bi_props


def test_the_core_readers_need_no_torch(monkeypatch):
    """A46 P1a. med_volume_stats used MONAI's LoadImage, which imports torch:
    505 MB installed and >60 s on first import - it had already timed out a
    live tool call. DICOM, NIfTI and numpy now dispatch directly. Simulated
    by hiding MONAI entirely."""
    import numpy as np

    from tee.fleet import med as _med

    monkeypatch.setattr(_med, "have", lambda mod: mod != "monai")
    import tempfile as _tf
    from pathlib import Path as _P

    d = _P(_tf.mkdtemp())
    vol = np.zeros((4, 4, 2), dtype=np.float32)
    vol[0, 0, 0] = 7.5
    np.save(d / "v.npy", vol)
    r = _med.volume_stats({"path": str(d / "v.npy")})
    assert r["max"] == pytest.approx(7.5)
    assert r["voxels"] == 32
    assert "torch" not in repr(r)


def test_a_dicom_without_pixels_says_so_rather_than_crashing():
    """RTSTRUCT, SR and encapsulated PDF are everywhere in a real archive
    and carry no image."""
    from tee.fleet import med as _med

    assert "med_no_pixels" in pathlib.Path(_med.__file__).read_text()
