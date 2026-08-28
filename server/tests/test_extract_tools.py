"""End-to-end ex_* flow through the real registry/jobs: ingest a mixed
folder, read facts, in-band writeback, registration ops, media views."""

import time

import pytest
from fixtures_extract import DJI_SRT, make_dxf, make_pdf, make_scene_frames, make_video

from tee.app import TeeApp
from tee.extract.tools import register_extract_tools
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError


@pytest.fixture(scope="module")
def media_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("site-materials")
    make_dxf(directory / "plan.dxf")
    make_pdf(directory / "A-101.pdf")
    frames = make_scene_frames(tmp_path_factory.mktemp("frames"))
    make_video(directory / "walkthrough.mp4", frames)
    (directory / "flight.srt").write_text(DJI_SRT)
    from test_extract_images_media import make_photo

    for i, seed in enumerate((0, 1, 40)):
        make_photo(directory / f"photo{i}.jpg", seed=seed)
    return directory


@pytest.fixture(scope="module")
def app(tmp_path_factory, media_dir):
    project = tmp_path_factory.mktemp("project")
    application = TeeApp({"fake": FakeAdapter()}, project_root=project)
    application._extract = register_extract_tools(application, project)
    out = application.registry.call("ex_ingest", {"path": str(media_dir)})
    deadline = time.time() + 300
    while time.time() < deadline:
        status = application.jobs.status(out["job"])
        if status["state"] in ("done", "error"):
            break
        time.sleep(0.3)
    assert status["state"] == "done", status
    application._ingest_report = status["result"]
    yield application
    application.shutdown()


def test_ingest_report(app):
    report = app._ingest_report
    assert report["ingested"] == 7  # dxf, pdf, video, srt, 3 photos
    assert report["errors"] == []
    assert report.get("photo_groups") == 2
    assert report.get("contact_sheet")


def test_reingest_is_noop(app, media_dir):
    out = app.registry.call("ex_ingest", {"path": str(media_dir)})
    deadline = time.time() + 60
    while time.time() < deadline:
        status = app.jobs.status(out["job"])
        if status["state"] in ("done", "error"):
            break
        time.sleep(0.2)
    assert status["result"]["ingested"] == 0
    assert status["result"]["cached"] >= 6


def test_sources_and_facts(app):
    sources = app.registry.call("ex_sources", {})
    assert sources["total"] >= 6
    by_name = {s["name"]: s for s in sources["sources"]}
    assert by_name["plan.dxf"]["type"] == "cad"

    dxf_facts = app.registry.call("ex_facts", {"source": "plan.dxf", "kind": "plan"})
    assert dxf_facts["total"] == 1
    summary = dxf_facts["facts"][0]["plan"]
    assert summary["walls"] == 5

    keyframes = app.registry.call("ex_facts", {"source": "walkthrough.mp4", "kind": "keyframe"})
    assert keyframes["total"] >= 2

    flight = app.registry.call("ex_facts", {"source": "flight.srt", "kind": "flight_path"})
    assert flight["total"] == 1


def test_search_across_sources(app):
    hits = app.registry.call("ex_search", {"query": "bedroom"})["items"]
    assert any(h["name"] == "plan.dxf" for h in hits)


def test_in_band_writeback_requirements(app):
    # simulate the host model doing the in-band pass from ex_prepare guidance
    packet = app.registry.call("ex_prepare", {"source": "plan.dxf"})
    assert packet["media_type"] == "cad"
    assert "ex_store_facts" in str(packet)

    stored = app.registry.call(
        "ex_store_facts",
        {
            "source": "plan.dxf",
            "extractor": "requirements",
            "facts": [
                {
                    "kind": "requirement",
                    "tier": "stated_requirement",
                    "topic": "bedrooms",
                    "statement": "four bedrooms",
                    "quote": "four bedrooms",
                }
            ],
        },
    )
    assert stored["stored"] == 1
    hits = app.registry.call("ex_search", {"query": "four bedrooms"})["items"]
    assert any(h["fact"]["kind"] == "requirement" for h in hits)


def test_store_facts_validates_plans(app):
    with pytest.raises(TeeError) as err:
        app.registry.call(
            "ex_store_facts",
            {
                "source": "plan.dxf",
                "extractor": "vlm-document",
                "facts": [{"kind": "plan", "plan": {"schema": "wrong"}}],
            },
        )
    assert err.value.code == "bad_plan"


def test_register_ops_and_units_conflict(app):
    app.registry.call("ex_register", {"op": "datum", "lat": -22.57, "lon": 17.083})
    app.registry.call("ex_register", {"op": "frame", "frame_id": "dwg:t:model", "kind": "drawing"})
    fit = app.registry.call(
        "ex_register",
        {
            "op": "fit",
            "from_frame": "dwg:t:model",
            "to_frame": "site:enu",
            "src_points": [[0, 0], [10, 0], [10, 5]],
            "dst_points": [[0, 0], [11, 0], [11, 5.5]],
            "fix_scale": 1.0,
        },
    )
    assert "units_conflict" in fit
    assert fit["fit"]["free_scale"] == pytest.approx(1.1, rel=0.02)


def test_media_view_backend(app):
    data, info = app.media_view("photo0.jpg", None, None, 300)
    assert data[:2] == b"\xff\xd8"
    assert info["tokens"] <= 300
    data, info = app.media_view("walkthrough.mp4", None, 3.0, 400)
    assert data[:2] == b"\xff\xd8"
    with pytest.raises(TeeError) as err:
        app.media_view("walkthrough.mp4", None, None, 400)
    assert err.value.code == "need_timestamp"
    with pytest.raises(TeeError) as err:
        app.media_view("plan.dxf", None, None, 400)
    assert err.value.code == "no_view"


def test_ifc_export_roundtrip(app):
    from tee.extract.handoff import register_handoff_tools

    # handoff tools registered against the same store (blender not needed
    # for the IFC path)
    store, registry = app._extract
    register_handoff_tools(app, store, registry)

    out = app.registry.call("ex_export_ifc", {"source": "plan.dxf"})
    assert out["walls"] == 5
    assert out["storeys"] == 1

    import ifcopenshell

    model = ifcopenshell.open(out["path"])
    assert len(model.by_type("IfcWall")) == 5
    assert len(model.by_type("IfcBuildingStorey")) == 1


def _run_ingest(application, path):
    out = application.registry.call("ex_ingest", {"path": str(path)})
    deadline = time.time() + 60
    while time.time() < deadline:
        status = application.jobs.status(out["job"])
        if status["state"] in ("done", "error"):
            return status
        time.sleep(0.2)
    raise AssertionError(f"ingest never finished: {status}")


def test_missing_optional_lane_dep_skips_file_with_fix(tmp_path, monkeypatch):
    """A lane whose optional dependency is absent skips THAT file with the
    exact fix in the report; the job finishes and other files still ingest
    (the installed-bundle reality: extras are not installed by default)."""
    from test_extract_images_media import make_photo

    from tee.extract import images

    media = tmp_path / "media"
    media.mkdir()
    make_photo(media / "photo.jpg", seed=3)
    make_dxf(media / "plan.dxf")

    def boom(path):
        raise ModuleNotFoundError("No module named 'imagehash'", name="imagehash")

    monkeypatch.setattr(images, "extract_image", boom)
    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path / "proj")
    register_extract_tools(application, tmp_path / "proj")
    try:
        status = _run_ingest(application, media)
        assert status["state"] == "done", status
        report = status["result"]
        assert report["ingested"] == 1  # the DXF still made it
        assert len(report["skipped"]) == 1
        line = report["skipped"][0]
        assert "photo.jpg" in line and "imagehash" in line and "extract" in line
        assert report["errors"] == []
    finally:
        application.shutdown()


def test_missing_tee_module_still_fails_loud(tmp_path, monkeypatch):
    """A ModuleNotFoundError for a tee-internal module is a bug, not a
    missing extra - the job must fail loudly, never report a polite skip."""
    from tee.extract import images

    media = tmp_path / "media"
    media.mkdir()
    from test_extract_images_media import make_photo

    make_photo(media / "photo.jpg", seed=4)

    def boom(path):
        raise ModuleNotFoundError("No module named 'tee.extract.gone'", name="tee.extract.gone")

    monkeypatch.setattr(images, "extract_image", boom)
    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path / "proj")
    register_extract_tools(application, tmp_path / "proj")
    try:
        status = _run_ingest(application, media)
        assert status["state"] == "error", status
        assert "tee.extract.gone" in status["error"]
    finally:
        application.shutdown()
