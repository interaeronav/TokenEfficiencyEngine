"""Where a rigged body lands in the world: on its own midline, not on its mean.

`load_rigged_avatar` used to set `offset.x = -mean(x)` over the vertices, and
MEASURED 2026-09-04 that is not the midline of anything. This repo's character
is built on an x-grid, so its BOUNDS and its SKELETON are symmetric to the last
bit - but its Kuhn tetrahedral decomposition is HANDED, and the vertex mean
sits 5.0 mm off centre (a 1.80 m body at `cells_tall=48`). Centring on it put
the body 5.0 mm off, which `dressing.frame_from_mesh` read as arms at
-0.2404 / +0.2304 - 10.0 mm of asymmetry on a body that has none - against a
neck that function fixes at x = 0. That is exactly the asymmetry
`character.build_character`'s x-grid was written to remove, put back one layer
later by the loader.

A body's plane of symmetry is defined by its SKELETON. The mapping already
knows which bones are the left ones, so the midpoint of the mapped pairs is
the answer, with the BOUNDS midpoint as the fallback for a rig with no pair -
still the shape's own extremes rather than its triangle count's opinion.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from seamkiln.drape.dressing import frame_from_mesh
from seamkiln.rig.character import build_character
from seamkiln.rig.gltf_read import read_skinned_gltf
from seamkiln.rig.gltf_write import Skeleton, SkinnedPrimitive, write_glb
from seamkiln.rig.skin import _MIRROR_PAIRS, _plane_of_symmetry, load_rigged_avatar

H = 1.80
CELLS = 48  # the resolution every number in this file was measured at


@pytest.fixture(scope="module")
def character():
    return build_character(H, cells_tall=CELLS)


@pytest.fixture(scope="module")
def character_glb(tmp_path_factory: pytest.TempPathFactory, character) -> Path:
    path = tmp_path_factory.mktemp("placement") / "body.glb"
    write_glb(path, character.primitive(), character.skeleton)
    return path


def test_the_fixture_really_does_have_a_handed_mean(character_glb: Path) -> None:
    """The premise, measured before anything is asserted about the fix: this
    body's bounds and skeleton are exactly symmetric and its vertex mean is
    not. Without that, the rest of this file would be testing nothing."""
    rig = load_rigged_avatar(character_glb)
    x = rig.body.vertices[:, 0]
    assert abs(float(x.mean())) == pytest.approx(0.0050, abs=5e-4), "the tessellation is handed"
    assert float(x.min() + x.max()) == pytest.approx(0.0, abs=1e-9), "the bounds are not"
    for left, right in _MIRROR_PAIRS:
        gap = float(
            rig.body.joints[rig.slots[left]].rest[0, 3]
            + rig.body.joints[rig.slots[right]].rest[0, 3]
        )
        assert gap == pytest.approx(0.0, abs=1e-9), f"{left}/{right}"


def test_the_body_is_centred_on_its_skeleton_and_not_on_its_vertex_mean(
    character_glb: Path,
) -> None:
    """The fix, in the terms the defect was found in: what `frame_from_mesh`
    reads off the body once the loader has placed it."""
    rig = load_rigged_avatar(character_glb)
    assert float(rig.offset[0]) == pytest.approx(0.0, abs=1e-12)

    frame = frame_from_mesh(rig.mesh())
    left, right = float(frame.arms["l"][0][0]), float(frame.arms["r"][0][0])
    assert left + right == pytest.approx(0.0, abs=1e-9), f"arms at {left:+.4f} / {right:+.4f}"
    assert left == pytest.approx(-0.2354, abs=2e-3)
    # `frame_from_mesh` fixes the neck at x = 0, so the midline has to BE 0
    assert float(frame.neck[0]) == 0.0
    posed = rig.rest_vertices
    assert float(posed[:, 0].min() + posed[:, 0].max()) == pytest.approx(0.0, abs=1e-9)


def test_an_off_centre_body_is_brought_back_to_its_own_midline(character, tmp_path: Path) -> None:
    """A body modelled away from the origin is placed by its midline, and the
    handed mean is still 5 mm off it afterwards - which is the whole point:
    the two are different numbers and only one of them is the body's."""
    shift = np.asarray([0.5, 0.0, 0.0])
    path = tmp_path / "off_centre.glb"
    skeleton = character.skeleton
    write_glb(
        path,
        SkinnedPrimitive(
            positions=character.vertices + shift,
            normals=character.normals,
            indices=character.faces,
            joints=character.skin_joints,
            weights=character.skin_weights,
        ),
        Skeleton(
            names=skeleton.names,
            parents=skeleton.parents,
            positions=skeleton.positions + shift,
        ),
    )
    rig = load_rigged_avatar(path)
    assert float(rig.offset[0]) == pytest.approx(-0.5, abs=1e-9)
    x = rig.rest_vertices[:, 0]
    # 41 nm, which is float32 accessor storage of a body modelled half a metre
    # out - the same limit `test_the_bind_pose_is_the_identity` measures - and
    # not the arithmetic, which is exact on the centred fixture above.
    assert float(x.min() + x.max()) == pytest.approx(0.0, abs=1e-7)
    assert abs(float(x.mean())) == pytest.approx(0.0050, abs=5e-4)
    # and the ground placement is untouched by any of this
    assert float(rig.rest_vertices[:, 1].min()) == pytest.approx(0.0, abs=1e-9)


def test_the_fallback_is_the_bounds_midpoint_and_never_the_mean(character_glb: Path) -> None:
    """With no pair mapped there is no skeleton answer, and the fallback is
    still a shape's own extremes: 0.0 here, where the mean would say 5.0 mm."""
    body = read_skinned_gltf(character_glb)
    assert _plane_of_symmetry(body, {}) == pytest.approx(0.0, abs=1e-9)
    assert abs(float(body.vertices[:, 0].mean())) > 1e-3
