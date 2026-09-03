"""A67 acceptance A5 (round trip) and the two format traps doc 69 measured.

Both traps are silent by nature - the file writes fine, opens fine, and is
wrong by 250 mm - so they are pinned here rather than left as prose.
"""

from __future__ import annotations

import numpy as np
import pytest

from tee.kernel.errors import TeeError
from tee.pointcloud import io


@pytest.fixture(scope="module")
def cloud():
    rng = np.random.default_rng(7)
    points = rng.uniform([-3.0, -2.0, 0.0], [4.0, 5.0, 2.7], (20_000, 3))
    colors = rng.integers(0, 256, (20_000, 3)).astype(np.uint8)
    intensity = rng.integers(0, 65_536, 20_000).astype(np.uint16)
    return points, colors, intensity


# -- A5 --------------------------------------------------------------------


@pytest.mark.parametrize("fmt", ["ply", "las", "laz"])
def test_a5_round_trip_preserves_count_and_bbox(tmp_path, cloud, fmt):
    points, colors, _ = cloud
    written = io.write(points, tmp_path / f"rt.{fmt}", fmt, colors=colors)
    back = io.read(written["path"])
    assert len(back["points"]) == len(points)
    # PLY is origin-shifted on purpose; compare shape, then restore position
    recovered = back["points"]
    if fmt == "ply":
        recovered = recovered + np.asarray(written["origin_offset_m"])
    # float32 PLY resolves ~0.24 um here; LAS quantises at half a scale unit
    tolerance = 1e-5 if fmt == "ply" else io.LAS_SCALE
    assert np.allclose(recovered, points, atol=tolerance)
    assert np.allclose(recovered.min(axis=0), points.min(axis=0), atol=tolerance)
    assert np.allclose(recovered.max(axis=0), points.max(axis=0), atol=tolerance)


@pytest.mark.parametrize("fmt", ["ply", "las", "laz"])
def test_a5_colour_survives(tmp_path, cloud, fmt):
    points, colors, _ = cloud
    written = io.write(points, tmp_path / f"c.{fmt}", fmt, colors=colors)
    back = io.read(written["path"])
    assert "colors" in back
    assert np.array_equal(back["colors"][:, :3], colors)


def test_a5_intensity_survives_las(tmp_path, cloud):
    points, _, intensity = cloud
    written = io.write(points, tmp_path / "i.las", "las", intensity=intensity)
    back = io.read(written["path"])
    assert np.array_equal(back["intensity"], intensity)


def test_laz_is_lossless_against_las_and_smaller(tmp_path, cloud):
    points, _, _ = cloud
    las = io.write(points, tmp_path / "a.las", "las")
    laz = io.write(points, tmp_path / "a.laz", "laz")
    assert np.array_equal(io.read(las["path"])["points"], io.read(laz["path"])["points"])
    assert laz["bytes"] < las["bytes"]


# -- the traps -------------------------------------------------------------


def test_ply_export_is_origin_shifted_so_a_georeferenced_cloud_survives(tmp_path):
    """The 250 mm trap: trimesh writes float32, whose resolution is |x|*2^-23.

    ODM's odm_georeferenced_model.laz is georeferenced by construction, so
    this is the lane's real input, not a hypothetical.
    """
    rng = np.random.default_rng(0)
    local = rng.uniform([0, 0, 0], [4, 3, 2.7], (5_000, 3))
    utm = local + np.array([712_345.0, 8_034_567.0, 1_180.0])

    written = io.write(utm, tmp_path / "utm.ply", "ply")
    recovered = io.read(written["path"])["points"] + np.asarray(written["origin_offset_m"])
    assert np.abs(recovered - utm).max() < 1e-4, "origin shift must survive the round trip"

    # and prove the trap is real: writing the absolute coordinates loses 250 mm
    import trimesh

    raw = trimesh.PointCloud(utm).export(file_type="ply")
    (tmp_path / "raw.ply").write_bytes(raw)
    naive = np.asarray(trimesh.load(tmp_path / "raw.ply", process=False).vertices)
    assert np.abs(naive - utm).max() > 0.1, "if this stops failing, trimesh changed precision"


def test_las_scale_is_fine_enough_not_to_eat_the_tolerance_budget(tmp_path, cloud):
    """0.1 mm, not the conventional 1 mm - the file size is identical either way."""
    points, _, _ = cloud
    written = io.write(points, tmp_path / "s.las", "las")
    assert written["las_scale_m"] == 1e-4
    back = io.read(written["path"])["points"]
    assert np.abs(back - points).max() <= 5e-5 + 1e-12


def test_reader_reports_the_las_header_rather_than_assuming_a_scanner(tmp_path, cloud):
    points, _, _ = cloud
    written = io.write(points, tmp_path / "h.las", "las")
    back = io.read(written["path"])
    assert back["format"] == "las"
    assert back["point_format"] == 3
    assert str(back["las_version"]) == "1.4"


# -- refusals --------------------------------------------------------------


def test_unknown_extension_refuses_with_the_list(tmp_path):
    path = tmp_path / "scan.obj"
    path.write_text("v 0 0 0\n")
    with pytest.raises(TeeError) as exc:
        io.read(path)
    assert exc.value.code == "pc_unsupported_format"
    assert ".ply" in (exc.value.fix or "")


def test_missing_file_refuses(tmp_path):
    with pytest.raises(TeeError) as exc:
        io.read(tmp_path / "nope.ply")
    assert exc.value.code == "pc_missing_file"


def test_unwritable_format_refuses(tmp_path, cloud):
    points, _, _ = cloud
    with pytest.raises(TeeError) as exc:
        io.write(points, tmp_path / "x.obj", "obj")
    assert exc.value.code == "pc_unsupported_format"


def test_text_cloud_reads(tmp_path):
    rows = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    path = tmp_path / "c.xyz"
    np.savetxt(path, rows)
    assert np.allclose(io.read(path)["points"], rows)
