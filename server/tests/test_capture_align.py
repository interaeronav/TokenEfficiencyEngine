"""T3 on fakes: ICP registration parsing + the RMS gate refusing confident
misregistrations, the terrain-op parameter mapping, and every refusal
naming its fix. Live acceptance (real CloudCompare/qgis_process on a
planted transform and the real site DSM) is recorded in PROGRESS."""

from __future__ import annotations

import pytest

from tee.capture import align
from tee.kernel.errors import TeeError

CC_FAKE = """#!/bin/sh
log=""
prev=""
for a in "$@"; do
  [ "$prev" = "-LOG_FILE" ] && log="$a"
  prev="$a"
done
cat > "$log" <<'EOF'
[ICP] Convergence reached
Final RMS: {rms}
Transformation matrix:
0.999390 -0.034899 0.000000 0.050000
0.034899 0.999390 0.000000 0.020000
0.000000 0.000000 1.000000 0.000000
0.000000 0.000000 0.000000 1.000000
EOF
exit 0
"""

QGIS_FAKE = """#!/bin/sh
out=""
for a in "$@"; do
  case "$a" in OUTPUT=*) out="${a#OUTPUT=}" ;; esac
done
: > "$out"
printf '{"results": {"OUTPUT": "%s"}}\\n' "$out"
exit 0
"""


def _cc(tmp_path, rms="0.0123"):
    fake = tmp_path / "fake-cc"
    fake.write_text(CC_FAKE.replace("{rms}", rms))
    fake.chmod(0o755)
    return str(fake)


def _clouds(tmp_path):
    src = tmp_path / "src.xyz"
    dst = tmp_path / "dst.xyz"
    src.write_text("0 0 0\n1 0 0\n0 1 0\n")
    dst.write_text("0 0 0\n1 0 0\n0 1 0\n")
    return src, dst


def test_icp_parses_rms_and_matrix_and_states_the_frame(tmp_path):
    src, dst = _clouds(tmp_path)
    out = align.register_icp(src, dst, cfg={"cloudcompare": _cc(tmp_path)}, work_dir=tmp_path / "w")
    assert out["rms_m"] == 0.0123
    assert out["matrix"][0][3] == 0.05 and out["matrix"][1][3] == 0.02
    assert "design truth" in out["frame"] and "target untouched" in out["frame"]


def test_icp_gate_refuses_confident_misregistration(tmp_path):
    src, dst = _clouds(tmp_path)
    with pytest.raises(TeeError) as excinfo:
        align.register_icp(
            src, dst, cfg={"cloudcompare": _cc(tmp_path, rms="0.5")}, work_dir=tmp_path / "w"
        )
    assert excinfo.value.code == "capture_bad_registration"
    assert "0.5000" in excinfo.value.message and "0.050" in excinfo.value.message


def test_icp_refuses_when_no_convergence_line(tmp_path):
    src, dst = _clouds(tmp_path)
    fake = tmp_path / "fake-empty"
    fake.write_text(
        '#!/bin/sh\nprev=""\nfor a in "$@"; do'
        ' [ "$prev" = -LOG_FILE ] && : > "$a"; prev="$a"; done\nexit 0\n'
    )
    fake.chmod(0o755)
    with pytest.raises(TeeError) as excinfo:
        align.register_icp(src, dst, cfg={"cloudcompare": str(fake)}, work_dir=tmp_path / "w")
    assert excinfo.value.code == "capture_bad_registration"
    assert "converge" in excinfo.value.message


def test_explicit_wrong_binary_path_refuses_loudly(tmp_path):
    src, dst = _clouds(tmp_path)
    with pytest.raises(TeeError) as excinfo:
        align.register_icp(
            src, dst, cfg={"cloudcompare": str(tmp_path / "nope")}, work_dir=tmp_path / "w"
        )
    assert excinfo.value.code == "capture_cloudcompare_missing"
    assert "does not exist" in excinfo.value.message


def test_missing_inputs_refuse(tmp_path):
    with pytest.raises(TeeError) as excinfo:
        align.register_icp(tmp_path / "absent.xyz", tmp_path / "x", cfg={}, work_dir=tmp_path / "w")
    assert excinfo.value.code == "capture_align_missing_input"


def _qgis(tmp_path):
    fake = tmp_path / "fake-qgis"
    fake.write_text(QGIS_FAKE)
    fake.chmod(0o755)
    return str(fake)


def test_terrain_contours_and_diff_param_mapping(tmp_path):
    dem = tmp_path / "dsm.tif"
    dem.write_bytes(b"tif")
    out = align.terrain_op(
        "contours", dem, cfg={"qgis_process": _qgis(tmp_path)}, work_dir=tmp_path / "t",
        interval_m=0.5,
    )  # fmt: skip
    assert out["algorithm"] == "gdal:contour" and out["path"].endswith(".gpkg")

    with pytest.raises(TeeError) as excinfo:
        align.terrain_op(
            "dem_diff", dem, cfg={"qgis_process": _qgis(tmp_path)}, work_dir=tmp_path / "t"
        )
    assert "dem2" in excinfo.value.message
    out = align.terrain_op(
        "dem_diff", dem, cfg={"qgis_process": _qgis(tmp_path)}, work_dir=tmp_path / "t",
        dem2=dem,
    )  # fmt: skip
    assert out["algorithm"] == "gdal:rastercalculator"


def test_unknown_terrain_op_names_the_menu(tmp_path):
    dem = tmp_path / "dsm.tif"
    dem.write_bytes(b"tif")
    with pytest.raises(TeeError) as excinfo:
        align.terrain_op("volcano", dem, cfg={}, work_dir=tmp_path / "t")
    assert "contours" in excinfo.value.fix and "hillshade" in excinfo.value.fix


CC_COLLAPSED = CC_FAKE.replace("Final RMS: {rms}", "Final RMS: 0.0000155").replace(
    "0.999390 -0.034899 0.000000 0.050000", "0.000001 0.000000 0.000000 0.300000"
).replace("0.034899 0.999390 0.000000 0.020000", "0.000000 0.000001 0.000000 -0.260000")


def test_degenerate_seven_dof_fit_refuses(tmp_path):
    # the T6 finding as a fixture: scale collapsed to ~0, impossible RMS
    src, dst = _clouds(tmp_path)
    fake = tmp_path / "fake-collapse"
    fake.write_text(CC_COLLAPSED)
    fake.chmod(0o755)
    with pytest.raises(TeeError) as excinfo:
        align.register_icp(
            src, dst, cfg={"cloudcompare": str(fake)}, work_dir=tmp_path / "w",
            adjust_scale=True,
        )  # fmt: skip
    assert excinfo.value.code == "capture_bad_registration"
    assert "Degenerate" in excinfo.value.message
    assert "scale references" in excinfo.value.fix
