"""A67 acceptance A6-A9: the tools end to end, through the real registry.

A8 is the one that justifies the module: no pc_* response may carry an array
longer than 64 elements or a string longer than 2 KB. If that ever breaks,
the lane has started dumping points into the model's context and the whole
premise is gone - so it fails the build.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from fixtures_pointcloud import make_room

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.pointcloud import io
from tee.pointcloud.store import MAX_ARRAY, MAX_STRING
from tee.pointcloud.tools import register_pointcloud_tools


@pytest.fixture(scope="module")
def scan(tmp_path_factory):
    """The synthetic room, written out as a real PLY the lane must open."""
    path = tmp_path_factory.mktemp("scans") / "room.ply"
    points, truth = make_room()
    io.write(points, path, "ply")
    # PLY is origin-shifted by design; give the test the offset it needs
    return path, truth


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    project = tmp_path_factory.mktemp("project")
    application = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_pointcloud_tools(application, project)
    try:
        yield application
    finally:
        application.shutdown()


def call(_app, _tool, **args):
    """Positional-only wrapper: pc_control_add takes its own `name` argument."""
    return _app.registry.call(_tool, args)


# -- A8: the invariant that justifies the lane -----------------------------


def _violations(payload, path="response"):
    out = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            out += _violations(value, f"{path}.{key}")
    elif isinstance(payload, (list, tuple)):
        if len(payload) > MAX_ARRAY:
            out.append(f"{path}: array of {len(payload)} (cap {MAX_ARRAY})")
        for i, value in enumerate(payload[:MAX_ARRAY]):
            out += _violations(value, f"{path}[{i}]")
    elif isinstance(payload, str) and len(payload.encode()) > MAX_STRING:
        out.append(f"{path}: string of {len(payload.encode())} bytes (cap {MAX_STRING})")
    return out


@pytest.fixture(scope="module")
def pipeline(app, scan):
    """The minimum viable subset, run once, with every response kept."""
    path, truth = scan
    responses = {}
    opened = responses["pc_open"] = call(app, "pc_open", path=str(path))
    cid = opened["cloud_id"]
    responses["pc_stat"] = call(app, "pc_stat", cloud_id=cid, what="z_histogram")
    levelled = responses["pc_level"] = call(app, "pc_level", cloud_id=cid)
    lid = levelled["cloud_id"]
    responses["pc_slice"] = call(app, "pc_slice", cloud_id=lid, z_m=1.2, out=["dxf", "svg"])
    # place the tape across the long axis using the levelled cloud's own extent
    bbox = call(app, "pc_stat", cloud_id=lid, what="extent")["bbox_m"]
    mid_y = (bbox[1] + bbox[4]) / 2
    mid_x = (bbox[0] + bbox[3]) / 2
    # Two baselines, because that is what okongo-capture-protocol.md 1 tells
    # the operator to do: one distance carries both plane fits' noise, and a
    # single 4 m tape measured off the bbox lands at ~500 ppm on its own.
    responses["pc_control_add"] = call(
        app,
        "pc_control_add",
        cloud_id=lid,
        name="long wall",
        p1=[bbox[0] + 0.05, mid_y, 1.2],
        p2=[bbox[3] - 0.05, mid_y, 1.2],
        true_mm=4000.0,
    )
    call(
        app,
        "pc_control_add",
        cloud_id=lid,
        name="short wall",
        p1=[mid_x, bbox[1] + 0.05, 1.2],
        p2=[mid_x, bbox[4] - 0.05, 1.2],
        true_mm=3000.0,
    )
    responses["pc_control_verify"] = call(app, "pc_control_verify", cloud_id=lid)
    responses["pc_export"] = call(app, "pc_export", cloud_id=lid, format="las")
    responses["pc_report"] = call(app, "pc_report", cloud_id=lid)
    return responses, truth


def test_a8_no_response_dumps_an_array_or_a_wall_of_text(pipeline):
    responses, _ = pipeline
    problems = []
    for name, payload in responses.items():
        if name.startswith("_"):
            continue
        problems += [f"{name}: {v}" for v in _violations(payload)]
    assert not problems, problems


def test_a8_holds_for_a_cloud_with_many_segments(app, scan):
    """The cap must survive a slice that finds more geometry than it can list."""
    path, _ = scan
    cid = call(app, "pc_open", path=str(path))["cloud_id"]
    lid = call(app, "pc_level", cloud_id=cid)["cloud_id"]
    out = call(app, "pc_slice", cloud_id=lid, z_m=1.2, fit="lines")
    assert not _violations(out)
    assert len(out["lengths_m"]) <= 32


# -- A7: the headline metric -----------------------------------------------


def test_a7_the_whole_sequence_fits_in_two_thousand_tokens(pipeline):
    responses, _ = pipeline
    sequence = ["pc_open", "pc_level", "pc_control_add", "pc_control_verify", "pc_slice"]
    total = sum(estimate_tokens(json.dumps(responses[n], default=str)) for n in sequence)
    assert total <= 2_000, f"{total} tokens across {sequence}"


@pytest.mark.parametrize(
    ("tool", "budget"),
    [
        ("pc_open", 150),
        ("pc_stat", 250),
        ("pc_level", 200),
        ("pc_control_add", 100),
        ("pc_control_verify", 300),
        ("pc_slice", 300),
        ("pc_report", 400),
    ],
)
def test_each_response_stays_inside_its_contract_budget(pipeline, tool, budget):
    responses, _ = pipeline
    cost = estimate_tokens(json.dumps(responses[tool], default=str))
    assert cost <= budget, f"{tool} cost {cost} tokens, budget {budget}"


# -- A6: the DXF is real ---------------------------------------------------


def test_a6_dxf_is_metres_with_insunits_six(pipeline):
    import ezdxf

    responses, _ = pipeline
    doc = ezdxf.readfile(responses["pc_slice"]["paths"]["dxf"])
    # 6 = metres. A template at the wrong scale is worse than no template.
    assert doc.header["$INSUNITS"] == 6


def test_a6_a_segment_measured_in_the_dxf_matches_the_reported_length(pipeline):
    import ezdxf

    responses, _ = pipeline
    doc = ezdxf.readfile(responses["pc_slice"]["paths"]["dxf"])
    drawn = []
    for entity in doc.modelspace():
        pts = [(p[0], p[1]) for p in entity.get_points()]
        drawn.append(float(np.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])))
    reported = sorted(responses["pc_slice"]["lengths_m"])
    assert len(drawn) == responses["pc_slice"]["segments"]
    for measured, said in zip(sorted(drawn), reported, strict=True):
        assert measured == pytest.approx(said, abs=0.001), "1 mm gate"


def test_svg_declares_a_scale_and_carries_a_reference_square(pipeline):
    responses, _ = pipeline
    svg = Path(responses["pc_slice"]["paths"]["svg"]).read_text()
    assert "mm" in svg and "1 m reference square" in svg and "1:50" in svg


# -- the pipeline's own answers --------------------------------------------


def test_open_reports_what_it_found_not_what_it_assumed(pipeline):
    responses, _ = pipeline
    opened = responses["pc_open"]
    assert opened["count"] == 279_352
    assert opened["format"] == "ply"
    assert opened["spacing_mm"] > 0
    assert "cloud_id" in opened


def test_level_and_control_agree_with_the_fixture(pipeline):
    responses, truth = pipeline
    assert responses["pc_level"]["residual_tilt_deg"] <= 0.05
    factor = responses["pc_control_verify"]["suggested_scale"]
    error_ppm = abs(factor - truth["correction"]) / truth["correction"] * 1e6
    assert error_ppm <= 500


def test_every_mutation_mints_a_new_cloud_with_a_recorded_parent(app, scan):
    path, _ = scan
    first = call(app, "pc_open", path=str(path))["cloud_id"]
    second = call(app, "pc_level", cloud_id=first)
    assert second["cloud_id"] != first
    assert second["parent"] == first
    # the original is still openable - every step is reversible
    assert call(app, "pc_stat", cloud_id=first, what="extent")["count"] == 279_352


def test_report_gives_a_verdict_and_a_path(pipeline):
    responses, _ = pipeline
    report = responses["pc_report"]
    assert report["verdict"] in {
        "TRUSTWORTHY",
        "USABLE",
        "SHAPE ONLY",
        "UNRELIABLE",
        "UNVERIFIED",
        "NOT READY",
    }
    assert report["path"].endswith("-qa.md")
    sheet = Path(report["path"]).read_text()
    assert "capture_register" in sheet, "the sheet must point registration at the lane that owns it"
    assert "Control baselines" in sheet


def test_report_says_unverified_when_no_tape_was_recorded(app, scan):
    path, _ = scan
    cid = call(app, "pc_open", path=str(path))["cloud_id"]
    lid = call(app, "pc_level", cloud_id=cid)["cloud_id"]
    assert call(app, "pc_report", cloud_id=lid)["verdict"] == "UNVERIFIED"


# -- refusals --------------------------------------------------------------


def test_unknown_cloud_id_refuses_with_the_fix(app):
    with pytest.raises(TeeError) as exc:
        call(app, "pc_stat", cloud_id="pc_deadbeef01", what="extent")
    assert exc.value.code == "pc_unknown_cloud"
    assert "pc_open" in (exc.value.fix or "")


def test_bad_units_refuses_listing_the_real_ones(app, scan):
    path, _ = scan
    with pytest.raises(TeeError) as exc:
        call(app, "pc_open", path=str(path), units="furlong")
    assert exc.value.code == "pc_bad_units"
    assert "mm" in (exc.value.fix or "")


def test_implausible_scale_is_called_a_units_error(app, scan):
    path, _ = scan
    cid = call(app, "pc_open", path=str(path))["cloud_id"]
    with pytest.raises(TeeError) as exc:
        call(app, "pc_scale_apply", cloud_id=cid, factor=1000.0)
    assert exc.value.code == "pc_implausible_scale"


def test_unknown_stat_topic_refuses(app, scan):
    path, _ = scan
    cid = call(app, "pc_open", path=str(path))["cloud_id"]
    with pytest.raises(TeeError) as exc:
        call(app, "pc_stat", cloud_id=cid, what="vibes")
    assert exc.value.code == "pc_unknown_stat"
    assert "z_histogram" in (exc.value.fix or "")


# -- A9: headless ----------------------------------------------------------


def test_a9_the_whole_lane_runs_with_no_dcc_connected(app, pipeline):
    """Nothing above touched an adapter; this states it rather than implying it."""
    responses, _ = pipeline
    assert responses["pc_report"]["verdict"]
    assert app.adapters.keys() == {"fake"}


def test_a9_e57_refuses_with_an_install_line_when_cloudcompare_is_absent(monkeypatch, tmp_path):
    import shutil

    monkeypatch.setattr(io, "_CC_DEFAULT", str(tmp_path / "nope"))
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(TeeError) as exc:
        io._cloudcompare()
    assert exc.value.code == "pc_cloudcompare_missing"
    assert "brew install" in (exc.value.fix or "")


def test_scaling_the_cloud_rescales_its_baselines_so_the_verdict_is_current(app, scan):
    """A baseline is a measurement OF the cloud, so it scales with the cloud.

    Carrying the parent's numbers forward unchanged made pc_report read
    pre-correction deltas and call a freshly corrected scan "SHAPE ONLY -
    do not scale off this drawing", which is the opposite of true.
    """
    path, _ = scan
    cid = call(app, "pc_open", path=str(path))["cloud_id"]
    lid = call(app, "pc_level", cloud_id=cid)["cloud_id"]
    box = call(app, "pc_stat", cloud_id=lid, what="extent")["bbox_m"]
    mid_y, mid_x = (box[1] + box[4]) / 2, (box[0] + box[3]) / 2
    call(
        app,
        "pc_control_add",
        cloud_id=lid,
        name="long wall",
        p1=[box[0] + 0.05, mid_y, 1.2],
        p2=[box[3] - 0.05, mid_y, 1.2],
        true_mm=4000.0,
    )
    call(
        app,
        "pc_control_add",
        cloud_id=lid,
        name="short wall",
        p1=[mid_x, box[1] + 0.05, 1.2],
        p2=[mid_x, box[4] - 0.05, 1.2],
        true_mm=3000.0,
    )

    before = call(app, "pc_report", cloud_id=lid)
    assert before["worst_control_mm"] > 10, "the uncorrected scan is off by centimetres"

    scaled = call(app, "pc_scale_apply", cloud_id=lid)["cloud_id"]
    after = call(app, "pc_report", cloud_id=scaled)
    assert after["worst_control_mm"] <= 2.0, after
    assert after["verdict"] == "TRUSTWORTHY", after


def test_a_rigid_transform_leaves_baselines_untouched(app, scan):
    """pc_level preserves distance, so its carried baselines must not move."""
    path, _ = scan
    cid = call(app, "pc_open", path=str(path))["cloud_id"]
    lid = call(app, "pc_level", cloud_id=cid)["cloud_id"]
    box = call(app, "pc_stat", cloud_id=lid, what="extent")["bbox_m"]
    mid_y = (box[1] + box[4]) / 2
    added = call(
        app,
        "pc_control_add",
        cloud_id=lid,
        name="wall",
        p1=[box[0] + 0.05, mid_y, 1.2],
        p2=[box[3] - 0.05, mid_y, 1.2],
        true_mm=4000.0,
    )
    again = call(app, "pc_level", cloud_id=lid)["cloud_id"]
    carried = call(app, "pc_control_verify", cloud_id=again)["baselines"][0]
    assert carried["measured_mm"] == added["measured_mm"]
