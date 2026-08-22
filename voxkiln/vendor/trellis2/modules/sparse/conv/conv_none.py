# voxkiln vendor addition: pure-PyTorch sparse submanifold conv backend.
# Interface-compatible with conv_flex_gemm (dispatched via config.CONV =
# 'none'). Derived from shivampkumar/trellis-mac backends/conv_none.py (MIT),
# with the O(K*N) Python-dict neighbor build replaced by a vectorized
# sorted-key searchsorted lookup - same semantics, no per-voxel Python loop.
# Works on MPS, CPU, and CUDA; slower than flex_gemm/spconv but portable.

import math

import torch
import torch.nn as nn

from .. import SparseTensor

_INT32_SPAN = 2**21  # per-axis coordinate span for the packed int64 key


def _pack_coords(coords: torch.Tensor) -> torch.Tensor:
    """Pack [N, 4] (batch, z, y, x) int coords into unique int64 keys.

    Coordinates are shifted by _INT32_SPAN//2 so negative neighbor probes
    still pack monotonically; 2^21 per axis leaves room for batch in the
    top bits (grids here are <= 1536^3).
    """
    c = coords.long() + (_INT32_SPAN // 2)
    return ((c[:, 0] * _INT32_SPAN + c[:, 1]) * _INT32_SPAN + c[:, 2]) * _INT32_SPAN + c[:, 3]


def _lookup(sorted_keys: torch.Tensor, order: torch.Tensor, query: torch.Tensor):
    """Return (indices, found) of query keys within the sorted key table."""
    n = sorted_keys.shape[0]
    pos = torch.searchsorted(sorted_keys, query)
    pos_c = pos.clamp(max=n - 1)
    found = sorted_keys[pos_c] == query
    return order[pos_c], found


def sparse_conv3d_init(self, in_channels, out_channels, kernel_size, stride=1, dilation=1, padding=None, bias=True, indice_key=None):
    assert stride == 1 and (padding is None), \
        "the 'none' backend only supports submanifold sparse convolution (stride=1, padding=None)"

    self.in_channels = in_channels
    self.out_channels = out_channels
    self.kernel_size = tuple(kernel_size) if isinstance(kernel_size, (list, tuple)) else (kernel_size,) * 3
    self.stride = tuple(stride) if isinstance(stride, (list, tuple)) else (stride,) * 3
    self.dilation = tuple(dilation) if isinstance(dilation, (list, tuple)) else (dilation,) * 3

    self.weight = nn.Parameter(torch.empty((out_channels, in_channels, *self.kernel_size)))
    if bias:
        self.bias = nn.Parameter(torch.empty(out_channels))
    else:
        self.register_parameter("bias", None)

    torch.nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
    if self.bias is not None:
        fan_in, _ = torch.nn.init._calculate_fan_in_and_fan_out(self.weight)
        if fan_in != 0:
            bound = 1 / math.sqrt(fan_in)
            torch.nn.init.uniform_(self.bias, -bound, bound)

    # Match flex_gemm weight layout: (Co, Ci, Kd, Kh, Kw) -> (Co, Kd, Kh, Kw, Ci)
    self.weight = nn.Parameter(self.weight.permute(0, 2, 3, 4, 1).contiguous())


def sparse_conv3d_forward(self, x: SparseTensor) -> SparseTensor:
    Co, Kd, Kh, Kw, Ci = self.weight.shape
    coords = x.coords
    feats = x.feats
    n = coords.shape[0]

    cache_key = f'SubMConv3d_none_neighbor_{Kw}x{Kh}x{Kd}_dilation{self.dilation}'
    neighbor_cache = x.get_spatial_cache(cache_key)

    if neighbor_cache is None:
        keys = _pack_coords(coords)
        order = keys.argsort()
        sorted_keys = keys[order]

        dz, dy, dx = self.dilation
        offsets = []
        for kz in range(Kd):
            for ky in range(Kh):
                for kx in range(Kw):
                    offsets.append(((kz - Kd // 2) * dz, (ky - Kh // 2) * dy, (kx - Kw // 2) * dx))
        offsets_t = torch.tensor(offsets, dtype=torch.long, device=coords.device)  # [K, 3]

        src_list, tgt_list, k_list = [], [], []
        base = coords.long()
        for k_idx in range(offsets_t.shape[0]):
            probe = base.clone()
            probe[:, 1:] += offsets_t[k_idx]
            src, found = _lookup(sorted_keys, order, _pack_coords(probe))
            tgt = torch.nonzero(found, as_tuple=False).squeeze(1)
            if tgt.numel() == 0:
                continue
            src_list.append(src[found])
            tgt_list.append(tgt)
            k_list.append(torch.full((tgt.numel(),), k_idx, dtype=torch.long, device=coords.device))

        if src_list:
            neighbor_cache = (torch.cat(src_list), torch.cat(tgt_list), torch.cat(k_list))
        else:
            empty = torch.empty(0, dtype=torch.long, device=coords.device)
            neighbor_cache = (empty, empty, empty)
        x.register_spatial_cache(cache_key, neighbor_cache)

    src_idx, tgt_idx, k_idx = neighbor_cache

    k_total = Kd * Kh * Kw
    w = self.weight.reshape(Co, k_total, Ci).permute(1, 2, 0)  # (K, Ci, Co)

    out = torch.zeros(n, Co, device=feats.device, dtype=feats.dtype)
    if src_idx.numel() > 0:
        for k in range(k_total):
            mask = k_idx == k
            if not bool(mask.any()):
                continue
            edge_out = feats[src_idx[mask]] @ w[k].to(feats.dtype)
            out.scatter_add_(0, tgt_idx[mask].unsqueeze(1).expand(-1, Co), edge_out)

    if self.bias is not None:
        out = out + self.bias.to(feats.dtype)

    return x.replace(out)


def sparse_inverse_conv3d_init(self, *args, **kwargs):
    raise NotImplementedError("SparseInverseConv3d is not implemented in the 'none' backend "
                              "(TRELLIS.2 uses no strided sparse convs)")


def sparse_inverse_conv3d_forward(self, x: SparseTensor) -> SparseTensor:
    raise NotImplementedError("SparseInverseConv3d is not implemented in the 'none' backend")
