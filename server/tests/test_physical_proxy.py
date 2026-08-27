"""CoACD proxy cache behavior (11.4 tier 1)."""

from __future__ import annotations

import pytest

pytest.importorskip("coacd")
trimesh = pytest.importorskip("trimesh")

from tee.kernel.errors import TeeError  # noqa: E402
from tee.physical.proxy import coacd_proxy  # noqa: E402


def _l_shape(path):
    """Concave L: two boxes fused - convex hull would swallow the notch."""
    a = trimesh.creation.box(extents=(2, 1, 1))
    b = trimesh.creation.box(extents=(1, 1, 2))
    b.apply_translation((-0.5, 0, 1.0))
    trimesh.util.concatenate([a, b]).export(str(path))
    return path


def test_concave_mesh_decomposes_and_caches(tmp_path):
    src = _l_shape(tmp_path / "l.stl")
    first = coacd_proxy(src, tmp_path / "proxies", threshold=0.05)
    assert first["cache_hit"] is False
    assert first["hulls"] >= 2, "an L-shape must not collapse to one hull"
    assert (tmp_path / "proxies").joinpath(first["cache_key"], "proxy.glb").is_file()

    second = coacd_proxy(src, tmp_path / "proxies", threshold=0.05)
    assert second["cache_hit"] is True
    assert second["hulls"] == first["hulls"]

    # different params -> different cache slot, honest recompute
    third = coacd_proxy(src, tmp_path / "proxies", threshold=0.2)
    assert third["cache_hit"] is False
    assert third["cache_key"] != first["cache_key"]


def test_missing_file_fails_loud(tmp_path):
    with pytest.raises(TeeError) as err:
        coacd_proxy(tmp_path / "nope.glb", tmp_path / "proxies")
    assert "Not a file" in str(err.value)
