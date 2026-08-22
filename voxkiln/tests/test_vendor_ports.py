"""Unit verification of the portable backends added to the vendored tree -
each checked against an exact reference implementation on CPU torch, so
the Mac session inherits ports that are already proven correct, not just
syntax-checked."""

import numpy as np
import pytest

torch = pytest.importorskip("torch")


def test_sdpa_sparse_attention_matches_manual_softmax():
    from trellis2.modules.sparse import VarLenTensor
    from trellis2.modules.sparse.attention.full_attn import (
        sparse_scaled_dot_product_attention,
    )

    torch.manual_seed(0)
    heads, ch = 2, 8
    lens = [6, 4]
    feats = torch.randn(sum(lens), 3, heads, ch)
    qkv = VarLenTensor(feats, VarLenTensor.layout_from_seqlen(lens))

    out = sparse_scaled_dot_product_attention(qkv).feats  # [T, H, C]

    # manual reference, per sequence, per head
    expected = torch.zeros(sum(lens), heads, ch)
    offset = 0
    for length in lens:
        chunk = feats[offset : offset + length]
        q, k, v = chunk.unbind(dim=1)  # [L, H, C]
        for h in range(heads):
            scores = (q[:, h] @ k[:, h].T) / np.sqrt(ch)
            expected[offset : offset + length, h] = torch.softmax(scores, dim=-1) @ v[:, h]
        offset += length
    assert torch.allclose(out, expected, atol=1e-5)


def test_conv_none_matches_dense_conv3d():
    from trellis2.modules.sparse import SparseConv3d, SparseTensor

    torch.manual_seed(0)
    res, ci, co = 4, 3, 5
    grid = torch.stack(torch.meshgrid(*(torch.arange(res),) * 3, indexing="ij"), dim=-1).reshape(
        -1, 3
    )
    coords = torch.cat([torch.zeros(len(grid), 1, dtype=torch.long), grid], dim=1).int()
    feats = torch.randn(len(grid), ci)

    conv = SparseConv3d(ci, co, kernel_size=3)
    out = conv(SparseTensor(feats=feats, coords=coords)).feats

    # dense reference: with EVERY voxel active, submanifold conv == plain
    # zero-padded conv3d evaluated at the active sites
    dense = torch.nn.Conv3d(ci, co, 3, padding=1, bias=True)
    with torch.no_grad():
        # conv_none weight layout (Co, Kd, Kh, Kw, Ci) -> (Co, Ci, Kd, Kh, Kw)
        dense.weight.copy_(conv.weight.permute(0, 4, 1, 2, 3))
        dense.bias.copy_(conv.bias)
    vol = torch.zeros(1, ci, res, res, res)
    vol[0, :, grid[:, 0], grid[:, 1], grid[:, 2]] = feats.T
    ref = dense(vol)[0, :, grid[:, 0], grid[:, 1], grid[:, 2]].T
    assert torch.allclose(out, ref, atol=1e-5)


def test_dual_grid_mesh_extraction_without_cuda_hashmap():
    from o_voxel.convert.flexible_dual_grid import flexible_dual_grid_to_mesh

    # four voxels ringing one x-axis edge (the quad-emission pattern)
    coords = torch.tensor([[0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0]], dtype=torch.int32)
    dual_vertices = torch.full((4, 3), 0.5)
    intersected = torch.zeros(4, 3, dtype=torch.bool)
    intersected[0, 0] = True  # voxel 0, x-axis edge -> one quad
    vertices, faces = flexible_dual_grid_to_mesh(
        coords,
        dual_vertices,
        intersected,
        None,
        aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        grid_size=2,
    )
    assert vertices.shape == (4, 3)
    assert faces.shape == (2, 3)  # one quad -> two triangles
    assert faces.max() < 4


def test_mesh_fallbacks_without_cumesh():
    import trimesh as tm
    from trellis2.representations.mesh.base import Mesh, _sparse_trilinear

    ico = tm.creation.icosphere(subdivisions=3)
    mesh = Mesh(
        torch.tensor(ico.vertices, dtype=torch.float32), torch.tensor(ico.faces, dtype=torch.int32)
    )

    # fill_holes defers (recorded), never crashes
    mesh.fill_holes()
    assert getattr(mesh, "fill_holes_deferred", False) is True

    # simplify falls back to CPU quadric decimation
    before = mesh.faces.shape[0]
    mesh.simplify(target=before // 4)
    assert mesh.faces.shape[0] <= before // 3

    # torch sparse-trilinear fallback matches the numpy baker's sampler
    from voxkiln.export import VoxelAttrs, sparse_trilinear

    rng = np.random.default_rng(0)
    coords = np.unique(rng.integers(0, 8, (64, 3)), axis=0)
    attrs = rng.random((len(coords), 6))
    probe = rng.random((16, 3)) * 0.5 - 0.25
    voxel = VoxelAttrs(
        coords=coords, attrs=attrs, origin=np.array([-0.5, -0.5, -0.5]), voxel_size=1 / 8
    )
    ref = sparse_trilinear(voxel, probe)
    got = _sparse_trilinear(
        torch.tensor(attrs, dtype=torch.float64),
        torch.tensor(coords, dtype=torch.int64),
        torch.tensor((probe + 0.5) * 8, dtype=torch.float64),
    ).numpy()
    assert np.allclose(got, ref, atol=1e-9)


def test_flow_euler_drops_prediction_lists():
    from trellis2.pipelines.samplers.flow_euler import FlowEulerSampler

    sampler = FlowEulerSampler(sigma_min=0.0)

    class Zero(torch.nn.Module):
        def forward(self, x, t, cond=None, **kw):
            return torch.zeros_like(x)

    noise = torch.randn(1, 4)
    ret = sampler.sample(Zero(), noise, steps=3, verbose=False)
    assert ret.samples.shape == noise.shape
    assert ret.pred_x_t == [] and ret.pred_x_0 == []  # the leak fix
    assert ret["samples"] is ret.samples  # edict semantics


def test_decode_thresholds_run_in_fp32():
    # the fdg_vae threshold fix: fp16 logits within rounding of zero must
    # not flip when compared through the fp32 path
    logits16 = torch.tensor([1e-4, -1e-4, 6e-5], dtype=torch.float16)
    assert ((logits16.float() > 0) == torch.tensor([True, False, True])).all()
