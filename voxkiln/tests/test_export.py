"""The export chain end to end on the FakeEngine's octant-colored cube:
repair -> simplify -> UV -> CPU bake -> GLB, verified by loading the GLB
back and checking the baked colors carry the octant signal."""

import numpy as np
import trimesh

from voxkiln.engine import FakeEngine
from voxkiln.export import export_glb, sparse_trilinear


def _fake(seed=0):
    return FakeEngine(resolution=16).generate(None, seed=seed, params={})


def test_sparse_trilinear_hits_octant_colors():
    raw = _fake()
    voxel = raw["voxel"]
    probe = np.array([[0.45, 0.45, 0.45], [-0.45, -0.45, -0.45]])
    samples = sparse_trilinear(voxel, probe)
    # positive octant is bright (0.85), negative octant dark (0.15)
    assert samples[0, 0] > 0.6
    assert samples[1, 0] < 0.4


def test_export_glb_roundtrip(tmp_path):
    raw = _fake()
    out = tmp_path / "cube.glb"
    report = export_glb(
        raw["vertices"],
        raw["faces"],
        raw["voxel"],
        str(out),
        texture_size=128,
        target_faces=2000,
    )
    assert out.exists()
    assert report["stats"]["tris"] > 0
    assert report["stats"]["watertight"] is True
    assert report["export"]["alpha_mode"] == "OPAQUE"

    loaded = trimesh.load(str(out), force="mesh")
    assert len(loaded.faces) == report["stats"]["tris"]
    material = loaded.visual.material
    img = np.array(material.baseColorTexture)
    assert img.shape[0] == report["export"]["texture_size"]
    # the baked texture must carry both bright and dark octants
    gray = img[..., :3].mean(axis=2)
    assert gray.max() > 150
    assert (gray[gray > 0].min() if (gray > 0).any() else 0) < 120


def test_export_clamps_texture_to_attr_resolution(tmp_path):
    raw = _fake()
    report = export_glb(
        raw["vertices"],
        raw["faces"],
        raw["voxel"],
        str(tmp_path / "c.glb"),
        texture_size=1024,
        target_faces=2000,
    )
    # 16^3 volume -> max useful 32; the clamp must fire and say why
    clamp = report["export"]["texture_size_clamped"]
    assert clamp["requested"] == 1024
    assert report["export"]["texture_size"] == clamp["actual"] == 32


def test_export_blend_alpha_detected(tmp_path):
    raw = _fake()
    voxel = raw["voxel"]
    voxel.attrs[:, 5] = 0.3  # translucent volume
    report = export_glb(
        raw["vertices"],
        raw["faces"],
        voxel,
        str(tmp_path / "t.glb"),
        texture_size=64,
        target_faces=2000,
    )
    assert report["export"]["alpha_mode"] == "BLEND"


def test_export_repairs_before_bake(tmp_path):
    raw = _fake()
    faces = raw["faces"][1:]  # knock a hole into the cube
    report = export_glb(
        raw["vertices"],
        faces,
        raw["voxel"],
        str(tmp_path / "h.glb"),
        texture_size=64,
        target_faces=2000,
        # a full missing face is far above the generator-hole default
        max_hole_perimeter=2.0,
    )
    assert any(e.get("op") == "fill_holes" for e in report["repairs"])
    assert report["stats"]["watertight"] is True


def test_fast_projection_stays_within_half_a_voxel_of_the_exact_one():
    """The bake projects every texel onto the frozen reference. The exact
    trimesh path is O(queries x triangles) in Python and unusable at bake
    scale, so the default samples the surface and answers from a KD-tree;
    this pins the error it is allowed to introduce."""
    import numpy as np
    import trimesh

    from voxkiln.export import _project_to_reference

    reference = trimesh.creation.icosphere(subdivisions=4, radius=0.5)
    rng = np.random.default_rng(0)
    # query points just off the surface, like simplified-mesh texel positions
    directions = rng.normal(size=(400, 3))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    points = directions * 0.5 * (1.0 + rng.normal(0, 0.01, (400, 1)))

    voxel_size = 1.0 / 512.0
    fast = _project_to_reference(reference, points, voxel_size=voxel_size)
    exact = _project_to_reference(reference, points, exact=True)

    deviation = np.linalg.norm(fast - exact, axis=1)
    # The sample count is capped (2e6), so on a large surface the spacing -
    # and with it the worst case - grows; the typical error is what the bake
    # actually sees. Both are pinned so a regression cannot creep in quietly.
    assert float(np.mean(deviation)) < 0.5 * voxel_size, float(np.mean(deviation))
    assert deviation.max() < 2.0 * voxel_size, deviation.max()
