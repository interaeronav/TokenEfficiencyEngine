"""A67 second pass: pc_crop, pc_clean, pc_ortho, pc_merge.

The two conditioning tools exist because the real Okongo scan needed them and
did not have them - `pc_slice` reported 3,843 points it could fit to no wall,
and the honest advice in that response was "crop and re-run". So these tests
check the two things that actually go wrong: that a subset keeps its colours
lined up with its points, and that a crop which removes almost everything
refuses instead of minting a cloud of eleven points.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fixtures_pointcloud import make_room

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.pointcloud import condition, merge, ortho
from tee.pointcloud.store import MAX_ARRAY, MAX_STRING, CloudStore
from tee.pointcloud.tools import register_pointcloud_tools


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    project = tmp_path_factory.mktemp("condition")
    application = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_pointcloud_tools(application, project)
    try:
        yield application
    finally:
        application.shutdown()


@pytest.fixture(scope="module")
def room(app):
    """A levelled room in the store, with colours, so subsetting is testable."""
    points, _ = make_room(tilt=(0.0, 0.0), yaw=0.0, scale=1.0, offset=(0.0, 0.0, 0.0))
    colors = np.zeros((len(points), 3), np.uint8)
    colors[:, 0] = np.clip(points[:, 2] * 90, 0, 255).astype(np.uint8)
    store = CloudStore(app.project_root)
    return store.mint(points, op="open", colors=colors), points, store


def call(app, tool, **args):
    return app.registry.call(tool, args)


# -- pc_crop ---------------------------------------------------------------


def test_a_z_crop_keeps_only_the_band(app, room):
    cid, points, _ = room
    out = call(app, "pc_crop", cloud_id=cid, z_range=[1.0, 1.5])
    expected = int(((points[:, 2] >= 1.0) & (points[:, 2] <= 1.5)).sum())
    assert out["kept"] == expected
    assert out["dropped"] == len(points) - expected
    assert out["cloud_id"] != cid and out["parent"] == cid


def test_a_box_and_a_z_range_combine(app, room):
    cid, _, _ = room
    both = call(app, "pc_crop", cloud_id=cid, box=[0, 0, 0, 2, 3, 2.7], z_range=[1.0, 1.5])
    only_z = call(app, "pc_crop", cloud_id=cid, z_range=[1.0, 1.5])
    assert both["kept"] < only_z["kept"]
    assert both["by"] == ["box", "z_range"]


def test_a_polygon_crop_matches_the_box_it_traces(app, room):
    """Ray casting, written out rather than pulled from shapely - so it is
    checked against a region whose answer is known independently."""
    cid, _, _ = room
    poly = call(app, "pc_crop", cloud_id=cid, polygon_xy=[[0.5, 0.5], [2, 0.5], [2, 2], [0.5, 2]])
    box = call(app, "pc_crop", cloud_id=cid, box=[0.5, 0.5, -99, 2, 2, 99])
    assert poly["kept"] == box["kept"]


def test_invert_drops_the_region_instead(app, room):
    cid, points, _ = room
    keep = call(app, "pc_crop", cloud_id=cid, z_range=[1.0, 1.5])
    drop = call(app, "pc_crop", cloud_id=cid, z_range=[1.0, 1.5], invert=True)
    assert keep["kept"] + drop["kept"] == len(points)


def test_a_crop_that_keeps_the_colours_keeps_them_ALIGNED(app, room):
    """The defect this catches is silent: colours subset with a different mask
    than the points, and every downstream image is wrong but plausible."""
    cid, _, store = room
    out = call(app, "pc_crop", cloud_id=cid, z_range=[1.0, 1.5])
    cropped = store.points(out["cloud_id"])
    colors = store.attr(out["cloud_id"], "rgb")
    assert colors is not None and len(colors) == len(cropped)
    assert np.array_equal(colors[:, 0], np.clip(cropped[:, 2] * 90, 0, 255).astype(np.uint8))


def test_a_crop_with_no_region_refuses(app, room):
    cid, _, _ = room
    with pytest.raises(TeeError, match="nothing to crop"):
        call(app, "pc_crop", cloud_id=cid)


def test_a_crop_that_would_leave_nothing_refuses(app, room):
    """Almost always a units error - a box in millimetres against a cloud in
    metres. Minting an eleven-point cloud would hide that until the DXF."""
    cid, _, _ = room
    with pytest.raises(TeeError, match="not a cloud"):
        call(app, "pc_crop", cloud_id=cid, box=[0, 0, 0, 0.01, 0.01, 0.01])


def test_a_six_less_box_is_named_as_such(app, room):
    cid, _, _ = room
    with pytest.raises(TeeError, match="six numbers"):
        call(app, "pc_crop", cloud_id=cid, box=[0, 0, 1, 1])


def test_a_crop_reaching_past_the_cloud_says_so(app, room):
    """The real trap, found by driving this on the Okongo scan: a PLY round
    trip origin-shifts, so a z_range of 0.05-2.35 m read as "floor to ceiling"
    and silently returned the top half of the room. The crop was right; the
    request was not; nothing said so."""
    cid, points, store = room
    shifted = store.mint(points - points.mean(axis=0), op="open")
    out = call(app, "pc_crop", cloud_id=shifted, z_range=[0.05, 2.35])
    assert "reaches past this cloud" in out["note"]
    assert "z is -1.4" in out["note"], "the note must quote the cloud's OWN extent"
    assert "note" not in call(app, "pc_crop", cloud_id=cid, z_range=[0.05, 2.35])


def test_a_crop_that_misses_the_cloud_entirely_is_named_differently(app, room):
    cid, _, _ = room
    with pytest.raises(TeeError, match="not a cloud"):
        call(app, "pc_crop", cloud_id=cid, z_range=[40.0, 50.0])


def test_a_crop_keeps_a_baseline_it_did_not_touch(app, room):
    """A crop moves no point, so a measurement whose two ends survive is still
    exactly true of the cropped cloud."""
    cid, _, store = room
    call(
        app,
        "pc_control_add",
        cloud_id=cid,
        name="width",
        p1=[0.02, 1.5, 1.2],
        p2=[3.98, 1.5, 1.2],
        true_mm=4000,
    )
    out = call(app, "pc_crop", cloud_id=cid, z_range=[0.9, 1.6])
    assert len(store.meta(out["cloud_id"])["controls"]) == 1
    assert "baseline" not in out.get("note", "")


def test_a_crop_drops_a_baseline_whose_picks_it_removed(app, room):
    """The Okongo defect. The reason to crop is usually that the snap found the
    wrong face - so carrying that reading forward poisons the verdict on the
    very cloud that was made to fix it. pc_control_verify then reported drift
    from a number measured on geometry this cloud no longer has."""
    cid, _, store = room
    call(
        app,
        "pc_control_add",
        cloud_id=cid,
        name="height",
        p1=[2.0, 1.5, 0.02],
        p2=[2.0, 1.5, 2.68],
        true_mm=2700,
    )
    out = call(app, "pc_crop", cloud_id=cid, z_range=[0.9, 1.6])
    surviving = {c["name"] for c in store.meta(out["cloud_id"])["controls"]}
    assert "height" not in surviving, "a floor-to-ceiling pick cannot survive a 0.9-1.6 m crop"
    assert "dropped 1 baseline" in out["note"] and "re-measure" in out["note"]


# -- pc_clean --------------------------------------------------------------


def test_clean_removes_planted_outliers_and_keeps_the_room(app, room):
    _, points, store = room
    rng = np.random.default_rng(3)
    strays = rng.uniform([-3, -3, -3], [7, 6, 6], size=(300, 3))
    noisy = store.mint(np.vstack([points, strays]), op="open")
    out = call(app, "pc_clean", cloud_id=noisy)
    assert out["outliers_removed"] >= 250, out
    survivors = store.points(out["cloud_id"])
    assert len(survivors) > 0.95 * len(points)


def test_a_voxel_grid_thins_the_cloud_and_reports_the_new_spacing(app, room):
    cid, _, _ = room
    out = call(app, "pc_clean", cloud_id=cid, sor=False, voxel_m=0.05)
    assert out["after"] < out["before"]
    coarse, fine = out["spacing_mm"][1], out["spacing_mm"][0]
    assert coarse > fine


def test_clean_asked_to_do_nothing_says_so(app, room):
    cid, _, _ = room
    with pytest.raises(TeeError, match="do nothing"):
        call(app, "pc_clean", cloud_id=cid, sor=False)


def test_voxel_downsampling_returns_points_the_scanner_actually_saw(room):
    """A centroid floats in mid-air across an edge; a real point does not."""
    _, points, _ = room
    idx = condition.voxel_downsample(points, 0.08)
    assert len(np.unique(idx)) == len(idx)
    assert np.isin(points[idx], points).all()


# -- pc_ortho --------------------------------------------------------------


def test_an_ortho_is_the_size_its_resolution_says(app, room):
    cid, points, _ = room
    out = call(app, "pc_ortho", cloud_id=cid, azimuth_deg=0.0, px_per_m=50)
    assert out["mm_per_pixel"] == 20.0
    assert out["pixels"][1] == pytest.approx(np.ptp(points[:, 2]) * 50 + 1, abs=1.5)
    assert Path(out["path"]).is_file()


def test_a_depth_limit_keeps_only_the_near_wall(app, room):
    cid, _, _ = room
    whole = call(app, "pc_ortho", cloud_id=cid, azimuth_deg=0.0, px_per_m=50)
    near = call(app, "pc_ortho", cloud_id=cid, azimuth_deg=0.0, px_per_m=50, depth_m=0.2)
    assert near["points_drawn"] < whole["points_drawn"]


def test_a_point_is_drawn_at_the_size_it_represents(app, room):
    """A 30 mm sample splatted into a 10 mm pixel gives a stipple that reads as
    a texture, not a surface - the complaint the depth rasters already drew.
    The dot is the footprint the sample actually covers, so nothing is
    invented and the facade becomes traceable."""
    cid, _, _ = room
    fine = call(app, "pc_ortho", cloud_id=cid, azimuth_deg=0.0, px_per_m=200)
    assert fine["dot_px"] > 1, "a cloud sampled coarser than the pixel needs a footprint"
    assert fine["coverage"] > 0.5


def test_two_depths_of_the_same_facade_do_not_overwrite_each_other(app, room):
    """The comparison is the whole point of the tool; one file would make it a
    comparison of an image with itself."""
    cid, _, _ = room
    shallow = call(app, "pc_ortho", cloud_id=cid, azimuth_deg=0.0, px_per_m=50, depth_m=0.2)
    deep = call(app, "pc_ortho", cloud_id=cid, azimuth_deg=0.0, px_per_m=50, depth_m=0.9)
    assert shallow["path"] != deep["path"]
    assert Path(shallow["path"]).is_file() and Path(deep["path"]).is_file()


def test_an_absurd_resolution_refuses_with_one_that_fits(app, room):
    """Fail loud and cheap: the refusal must carry the number that works."""
    cid, _, _ = room
    with pytest.raises(TeeError, match=r"px is \d+ MP") as raised:
        call(app, "pc_ortho", cloud_id=cid, azimuth_deg=0.0, px_per_m=10_000)
    assert "Lower px_per_m to about" in raised.value.fix


def test_the_scale_bar_is_in_the_pixels_not_beside_them(room, tmp_path):
    """A cropped, pasted, re-scaled copy of this image must still measure."""
    from PIL import Image

    _, points, _ = room
    out = tmp_path / "scalebar.png"
    ortho.render(points, out, azimuth_deg=0.0, px_per_m=60)
    pixels = np.asarray(Image.open(out))
    bar_band = pixels[-int(0.02 * 60) * 4 :, : int(60 * ortho.BAR_METRES * 1.1)]
    assert (bar_band == 0).any(), "no burnt-in scale bar in the bottom-left"


# -- pc_merge --------------------------------------------------------------


def test_merge_needs_at_least_two_clouds(app, room):
    cid, _, _ = room
    with pytest.raises(TeeError, match="got 1 cloud") as raised:
        call(app, "pc_merge", cloud_ids=[cid])
    assert "FIRST is the datum" in raised.value.fix


def test_overlap_is_measured_over_every_source_point(room):
    """CloudCompare's RMS is over the correspondences IT chose. This is the
    second opinion: a low RMS on 4% of the scan is two different rooms."""
    _, points, _ = room
    assert merge.overlap(points, points)["overlap"] == 1.0
    assert merge.overlap(points + 5.0, points)["overlap"] < 0.05
    partial = merge.overlap(points[points[:, 0] < 2.0] + np.array([0.0, 0.0, 0.0]), points)
    assert partial["overlap"] == 1.0 and partial["overlap_rms_mm"] == 0.0


# -- the invariant, over the new tools -------------------------------------


def _violations(payload, path="response"):
    out = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            out += _violations(value, f"{path}.{key}")
    elif isinstance(payload, (list, tuple)):
        if len(payload) > MAX_ARRAY:
            out.append(f"{path}: array of {len(payload)}")
        for i, value in enumerate(payload[:MAX_ARRAY]):
            out += _violations(value, f"{path}[{i}]")
    elif isinstance(payload, str) and len(payload.encode()) > MAX_STRING:
        out.append(f"{path}: string of {len(payload.encode())} bytes")
    return out


def test_no_new_tool_dumps_points_into_the_response(app, room):
    cid, _, _ = room
    responses = [
        call(app, "pc_crop", cloud_id=cid, z_range=[1.0, 1.5]),
        call(app, "pc_clean", cloud_id=cid, sor=False, voxel_m=0.05),
        call(app, "pc_ortho", cloud_id=cid, azimuth_deg=90.0, px_per_m=40),
    ]
    assert [v for r in responses for v in _violations(r)] == []


# -- a tape is held level --------------------------------------------------


def test_a_horizontal_baseline_measures_the_plan_distance(app, room):
    """On the Okongo scan there is no single height where both faces of Room 01
    are clean: the south side is a cabinet front below 930 mm and the north side
    is grazing-angle and sparse above it. The picks have to sit at different
    heights, and the straight 3D distance between them is then a diagonal - it
    read 90 mm long on a 3.95 m room. A tape is held level; so is this."""
    cid, _, _ = room
    slanted = dict(p1=[0.02, 1.5, 0.4], p2=[3.98, 1.5, 2.2], true_mm=4000)
    diagonal = call(app, "pc_control_add", cloud_id=cid, name="d", **slanted)
    plan = call(app, "pc_control_add", cloud_id=cid, name="h", horizontal=True, **slanted)
    assert plan["horizontal"] is True and diagonal["horizontal"] is False
    assert plan["measured_mm"] < diagonal["measured_mm"] - 300
    assert abs(plan["measured_mm"] - 4000) < 30, "the plan distance is the room's width"
